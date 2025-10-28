"""
Configuration management for Focus Guardian.

Implements a hierarchical configuration system with validation and self-healing:
1. config/default_config.json (version-controlled defaults)
2. data/config.encrypted.json (user overrides + encrypted API keys)
3. .env or config.yaml (developer settings)
4. Environment variables (highest priority)

Priority: ENV VARS > config.yaml > config.encrypted.json > default_config.json

Includes configuration validation, self-healing for corrupted configs, and runtime
validation to ensure the application remains stable even with invalid settings.
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv

from ..core.models import QualityProfile
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Config:
    """Configuration manager with hierarchical loading and encryption support."""
    
    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            root_dir: Project root directory (defaults to current working directory)
        """
        if root_dir is None:
            # Find project root (look for pyproject.toml)
            current = Path.cwd()
            while current != current.parent:
                if (current / "pyproject.toml").exists():
                    root_dir = current
                    break
                current = current.parent
            else:
                root_dir = Path.cwd()
        
        self.root_dir = Path(root_dir)
        self.config_dir = self.root_dir / "config"
        self.data_dir = self.root_dir / "data"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration layers
        load_dotenv()  # Load .env file if present
        
        self._default_config = self._load_default_config()
        self._user_config = self._load_user_config()
        self._developer_config = self._load_developer_config()
        
        # Encryption key for API keys (generate if not exists)
        self._encryption_key = self._get_or_create_encryption_key()
        
        logger.info(f"Configuration loaded from {self.root_dir}")

        # Validate and heal configuration after loading
        self._validate_and_heal_config()

    def _validate_and_heal_config(self) -> None:
        """Validate configuration integrity and repair corrupted files."""
        issues_found = []

        # Validate default config
        if not self._validate_config_structure(self._default_config):
            logger.warning("Default config has structural issues, regenerating...")
            issues_found.append("default_config")

        # Validate user config
        if not self._validate_config_structure(self._user_config):
            logger.warning("User config has structural issues, resetting to defaults...")
            issues_found.append("user_config")

        # Validate developer config
        if not self._validate_config_structure(self._developer_config):
            logger.warning("Developer config has structural issues, resetting...")
            issues_found.append("developer_config")

        # Attempt to heal corrupted configs
        if issues_found:
            self._heal_corrupted_configs(issues_found)

        # Validate final merged configuration
        try:
            # Test configuration system by accessing a known value
            test_value = self._get_config_value("snapshot_interval_sec", None)
            if test_value is None:
                logger.error("Configuration system validation failed")
                self._emergency_config_reset()
        except Exception as e:
            logger.error(f"Configuration system validation error: {e}")
            self._emergency_config_reset()

    def _validate_config_structure(self, config: Dict[str, Any]) -> bool:
        """Validate that a configuration dictionary has expected structure."""
        if not isinstance(config, dict):
            return False

        # Check for required keys and validate their types/values
        required_validations = {
            "snapshot_interval_sec": lambda x: isinstance(x, int) and 3 <= x <= 300,
            "video_bitrate_kbps_cam": lambda x: isinstance(x, int) and 100 <= x <= 5000,
            "video_bitrate_kbps_screen": lambda x: isinstance(x, int) and 100 <= x <= 10000,
            "video_res_profile": lambda x: x in ["Low", "Std", "High"],
            "max_parallel_uploads": lambda x: isinstance(x, int) and 1 <= x <= 10,
            "openai_vision_enabled": lambda x: isinstance(x, bool),
            "K_hysteresis": lambda x: isinstance(x, int) and 1 <= x <= 10,
            "min_span_minutes": lambda x: isinstance(x, (int, float)) and 0.1 <= x <= 10.0,
            "alert_sound_enabled": lambda x: isinstance(x, bool),
            "data_retention_days": lambda x: isinstance(x, int) and 1 <= x <= 365,
            "cloud_features_enabled": lambda x: isinstance(x, bool),
            "hume_ai_enabled": lambda x: isinstance(x, bool),
            "memories_ai_enabled": lambda x: isinstance(x, bool),
            "hume_ai_auto_upload": lambda x: isinstance(x, bool),
            "memories_ai_auto_upload": lambda x: isinstance(x, bool),
        }

        for key, validator in required_validations.items():
            if key in config:
                try:
                    if not validator(config[key]):
                        logger.warning(f"Invalid value for {key}: {config[key]}")
                        return False
                except Exception as e:
                    logger.warning(f"Error validating {key}: {e}")
                    return False

        return True

    def _heal_corrupted_configs(self, corrupted_files: list) -> None:
        """Heal corrupted configuration files by regenerating them."""
        if "default_config" in corrupted_files:
            # Regenerate default config
            default_config_path = self.config_dir / "default_config.json"
            try:
                default_config_path.unlink(missing_ok=True)  # Delete corrupted file
                self._default_config = self._load_default_config()  # Reload with defaults
                logger.info("Default config healed successfully")
            except Exception as e:
                logger.error(f"Failed to heal default config: {e}")

        if "user_config" in corrupted_files:
            # Reset user config to empty (will use defaults)
            user_config_path = self.data_dir / "config.encrypted.json"
            try:
                user_config_path.unlink(missing_ok=True)
                self._user_config = {}
                logger.info("User config healed successfully")
            except Exception as e:
                logger.error(f"Failed to heal user config: {e}")

        if "developer_config" in corrupted_files:
            # Reset developer config
            dev_config_path = self.root_dir / "config.yaml"
            try:
                dev_config_path.unlink(missing_ok=True)
                self._developer_config = {}
                logger.info("Developer config healed successfully")
            except Exception as e:
                logger.error(f"Failed to heal developer config: {e}")

    def _emergency_config_reset(self) -> None:
        """Emergency reset of all configuration if system is completely broken."""
        logger.critical("Configuration system emergency reset triggered")

        try:
            # Backup current configs before reset
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Reset all config files
            default_config_path = self.config_dir / "default_config.json"
            user_config_path = self.data_dir / "config.encrypted.json"
            dev_config_path = self.root_dir / "config.yaml"

            # Backup if they exist
            if default_config_path.exists():
                backup_path = self.data_dir / f"default_config.backup.{timestamp}.json"
                shutil.copy2(default_config_path, backup_path)

            if user_config_path.exists():
                backup_path = self.data_dir / f"config.encrypted.backup.{timestamp}.json"
                shutil.copy2(user_config_path, backup_path)

            if dev_config_path.exists():
                backup_path = self.data_dir / f"config.yaml.backup.{timestamp}"
                shutil.copy2(dev_config_path, backup_path)

            # Reset files
            default_config_path.unlink(missing_ok=True)
            user_config_path.unlink(missing_ok=True)
            dev_config_path.unlink(missing_ok=True)

            # Reload with fresh defaults
            self._default_config = self._load_default_config()
            self._user_config = {}
            self._developer_config = {}

            logger.info("Configuration emergency reset completed")

        except Exception as e:
            logger.critical(f"Emergency config reset failed: {e}")
            # If even emergency reset fails, we have bigger problems

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from config/default_config.json."""
        default_config_path = self.config_dir / "default_config.json"
        
        if not default_config_path.exists():
            # Create default config if it doesn't exist
            default_config = {
                "snapshot_interval_sec": 60,
                "video_bitrate_kbps_cam": 500,
                "video_bitrate_kbps_screen": 1000,
                "video_res_profile": "Std",
                "max_parallel_uploads": 3,
                "openai_vision_enabled": True,
                "K_hysteresis": 3,
                "min_span_minutes": 1.0,
                "alert_sound_enabled": True,
                "data_retention_days": 30,
                "cloud_features_enabled": False,
                "hume_ai_enabled": False,
                "memories_ai_enabled": False,
                "hume_ai_auto_upload": False,
                "memories_ai_auto_upload": False
            }
            
            with open(default_config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default config at {default_config_path}")
            return default_config
        
        with open(default_config_path, 'r') as f:
            return json.load(f)
    
    def _load_user_config(self) -> Dict[str, Any]:
        """Load user configuration from data/config.encrypted.json."""
        user_config_path = self.data_dir / "config.encrypted.json"
        
        if not user_config_path.exists():
            logger.debug("No user config found, using defaults")
            return {}
        
        try:
            with open(user_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load user config: {e}")
            return {}
    
    def _load_developer_config(self) -> Dict[str, Any]:
        """Load developer settings from config.yaml if present."""
        dev_config_path = self.root_dir / "config.yaml"
        
        if not dev_config_path.exists():
            logger.debug("No developer config found")
            return {}
        
        try:
            with open(dev_config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load developer config: {e}")
            return {}
    
    def _get_or_create_encryption_key(self) -> Fernet:
        """Get or create encryption key for API keys."""
        key_file = self.data_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Secure the key file (Unix-like systems)
            if os.name != 'nt':  # Not Windows
                os.chmod(key_file, 0o600)
            logger.info(f"Generated new encryption key at {key_file}")
        
        return Fernet(key)
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with priority hierarchy.
        
        Priority: ENV VARS > config.yaml > config.encrypted.json > default_config.json
        """
        # 1. Environment variable (highest priority)
        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        # 2. Developer config (config.yaml)
        if key in self._developer_config:
            return self._developer_config[key]
        
        # 3. User config (config.encrypted.json)
        if key in self._user_config:
            return self._user_config[key]
        
        # 4. Default config
        if key in self._default_config:
            return self._default_config[key]
        
        return default
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Public method to get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._get_config_value(key, default)
    
    # ========================================================================
    # Public API - Core Settings
    # ========================================================================
    
    def get_snapshot_interval_sec(self) -> int:
        """Get snapshot interval in seconds (default: 60, min: 3)."""
        value = self._get_config_value("snapshot_interval_sec", 60)
        return max(3, int(value))  # Enforce minimum of 3 seconds

    # --------------------------------------------------------------------
    # Agentic: Close app after consecutive distractions
    # --------------------------------------------------------------------
    def get_agent_close_app_enabled(self) -> bool:
        return bool(self._get_config_value("agent_close_app_enabled", False))

    def get_agent_close_app_consecutive_distractions(self) -> int:
        return int(self._get_config_value("agent_close_app_consecutive_distractions", 2))

    def get_agent_close_app_window_sec(self) -> int:
        return int(self._get_config_value("agent_close_app_window_sec", 60))

    def get_agent_close_scope(self) -> str:
        return str(self._get_config_value("agent_close_scope", "frontmost"))

    def get_agent_close_blocklist(self) -> list:
        val = self._get_config_value("agent_close_blocklist", [])
        return list(val) if isinstance(val, (list, tuple)) else []

    def get_agent_close_prompt_countdown_sec(self) -> int:
        return int(self._get_config_value("agent_close_prompt_countdown_sec", 0))
    
    def set_agent_close_app_enabled(self, enabled: bool) -> None:
        """Save agent close app enabled setting to user config.
        
        Args:
            enabled: Whether to enable the agentic app-close feature
        """
        self._user_config["agent_close_app_enabled"] = enabled
        
        # Save to config file
        user_config_path = self.data_dir / "config.encrypted.json"
        try:
            import json
            with open(user_config_path, 'w') as f:
                json.dump(self._user_config, f, indent=2)
            logger.info(f"Agent close app enabled: {enabled}")
        except Exception as e:
            logger.error(f"Failed to save agent config: {e}")
    
    # --------------------------------------------------------------------
    # Focus Duration Analyzer
    # --------------------------------------------------------------------
    def is_focus_analyzer_enabled(self) -> bool:
        """Check if focus duration analyzer is enabled."""
        value = self._get_config_value("focus_analyzer_enabled", True)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)
    
    def get_focus_analyzer_min_sessions(self) -> int:
        """Get minimum sessions needed for focus duration analysis."""
        return int(self._get_config_value("focus_analyzer_min_sessions", 3))
    
    def get_focus_analyzer_lookback_days(self) -> int:
        """Get lookback window in days for focus duration analysis."""
        return int(self._get_config_value("focus_analyzer_lookback_days", 30))
    
    def get_focus_analyzer_recommendation_factor(self) -> float:
        """Get recommendation factor (0.0-1.0) for focus duration suggestions."""
        return float(self._get_config_value("focus_analyzer_recommendation_factor", 0.75))
    
    def get_video_bitrate_kbps_cam(self) -> int:
        """Get camera video bitrate in kbps."""
        return int(self._get_config_value("video_bitrate_kbps_cam", 500))
    
    def get_video_bitrate_kbps_screen(self) -> int:
        """Get screen video bitrate in kbps."""
        return int(self._get_config_value("video_bitrate_kbps_screen", 1000))
    
    def get_video_res_profile(self) -> QualityProfile:
        """Get quality profile: Low | Std | High."""
        profile_str = self._get_config_value("video_res_profile", "Std")
        try:
            return QualityProfile(profile_str)
        except ValueError:
            logger.warning(f"Invalid quality profile '{profile_str}', using Std")
            return QualityProfile.STD
    
    def get_max_parallel_uploads(self) -> int:
        """Get maximum parallel upload workers (default: 3)."""
        return int(self._get_config_value("max_parallel_uploads", 3))
    
    def is_openai_vision_enabled(self) -> bool:
        """Check if OpenAI Vision API is enabled (default: True)."""
        value = self._get_config_value("openai_vision_enabled", True)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)
    
    def get_K_hysteresis(self) -> int:
        """Get K value for hysteresis voting (default: 3)."""
        return int(self._get_config_value("K_hysteresis", 3))
    
    def get_min_span_minutes(self) -> float:
        """Get minimum span in minutes for debounce (default: 1.0)."""
        return float(self._get_config_value("min_span_minutes", 1.0))

    def get_camera_index(self) -> int:
        """
        Get camera index for webcam capture.

        Returns:
            Camera index (0+ for specific camera, defaults to 0 on first run)
        """
        return int(self._get_config_value("camera_index", 0))

    def get_camera_name(self) -> str:
        """Get human-readable camera name."""
        return str(self._get_config_value("camera_name", "Auto-detect (FaceTime HD)"))

    def set_camera_config(self, camera_index: int, camera_name: str) -> None:
        """
        Save camera selection to user config.

        Args:
            camera_index: Camera index (0+ for specific camera)
            camera_name: Human-readable camera name
        """
        self._user_config["camera_index"] = camera_index
        self._user_config["camera_name"] = camera_name

        # Save to config file
        user_config_path = self.data_dir / "config.encrypted.json"
        try:
            with open(user_config_path, 'w') as f:
                json.dump(self._user_config, f, indent=2)
            logger.info(f"Camera config saved: {camera_name} (index {camera_index})")
        except Exception as e:
            logger.error(f"Failed to save camera config: {e}")

    # ========================================================================
    # Public API - API Keys
    # ========================================================================
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key (encrypted in storage, plaintext in env)."""
        # Try environment variable first
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            # Strip any quotes (including smart quotes) and whitespace
            env_key = env_key.strip().strip('"\'').strip('\u2018\u2019\u201c\u201d')
            return env_key
        
        # Try encrypted storage
        encrypted_key = self._user_config.get("openai_api_key_encrypted")
        if encrypted_key:
            try:
                return self._encryption_key.decrypt(encrypted_key.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt OpenAI API key: {e}")
                return None
        
        return None
    
    def get_hume_api_key(self) -> Optional[str]:
        """Get Hume AI API key."""
        env_key = os.getenv("HUME_API_KEY")
        if env_key:
            # Strip any quotes and whitespace
            env_key = env_key.strip().strip('"\'').strip('\u2018\u2019\u201c\u201d')
            return env_key
        
        encrypted_key = self._user_config.get("hume_api_key_encrypted")
        if encrypted_key:
            try:
                return self._encryption_key.decrypt(encrypted_key.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt Hume API key: {e}")
                return None
        
        return None
    
    def get_memories_api_key(self) -> Optional[str]:
        """Get Memories.ai API key."""
        env_key = os.getenv("MEM_AI_API_KEY")
        if env_key:
            # Strip any quotes and whitespace
            env_key = env_key.strip().strip('"\'').strip('\u2018\u2019\u201c\u201d')
            return env_key
        
        encrypted_key = self._user_config.get("memories_api_key_encrypted")
        if encrypted_key:
            try:
                return self._encryption_key.decrypt(encrypted_key.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt Memories.ai API key: {e}")
                return None
        
        return None
    
    def get_google_credentials(self) -> Optional[Dict[str, str]]:
        """Get Google OAuth credentials."""
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if client_id and client_secret:
            return {"client_id": client_id, "client_secret": client_secret}

        return None

    # ========================================================================
    # Public API - Cloud Features Configuration
    # ========================================================================

    def is_cloud_features_enabled(self) -> bool:
        """Check if cloud features are globally enabled (master switch)."""
        value = self._get_config_value("cloud_features_enabled", False)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def is_hume_ai_enabled(self) -> bool:
        """Check if Hume AI emotion analysis is enabled."""
        # Must have both cloud features enabled AND Hume AI specifically enabled
        if not self.is_cloud_features_enabled():
            return False
        value = self._get_config_value("hume_ai_enabled", False)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def is_memories_ai_enabled(self) -> bool:
        """Check if Memories.ai pattern analysis is enabled."""
        # Must have both cloud features enabled AND Memories AI specifically enabled
        if not self.is_cloud_features_enabled():
            return False
        value = self._get_config_value("memories_ai_enabled", False)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def is_hume_ai_auto_upload(self) -> bool:
        """Check if Hume AI should auto-upload after each session."""
        value = self._get_config_value("hume_ai_auto_upload", False)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def is_memories_ai_auto_upload(self) -> bool:
        """Check if Memories.ai should auto-upload after each session."""
        value = self._get_config_value("memories_ai_auto_upload", False)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)

    def set_cloud_features_enabled(self, enabled: bool) -> None:
        """Set cloud features master switch."""
        self._user_config["cloud_features_enabled"] = enabled
        self._save_user_config()
        logger.info(f"Cloud features {'enabled' if enabled else 'disabled'}")

    def set_hume_ai_enabled(self, enabled: bool) -> None:
        """Enable/disable Hume AI emotion analysis."""
        self._user_config["hume_ai_enabled"] = enabled
        self._save_user_config()
        logger.info(f"Hume AI {'enabled' if enabled else 'disabled'}")

    def set_memories_ai_enabled(self, enabled: bool) -> None:
        """Enable/disable Memories.ai pattern analysis."""
        self._user_config["memories_ai_enabled"] = enabled
        self._save_user_config()
        logger.info(f"Memories.ai {'enabled' if enabled else 'disabled'}")

    def set_hume_ai_auto_upload(self, enabled: bool) -> None:
        """Enable/disable Hume AI auto-upload."""
        self._user_config["hume_ai_auto_upload"] = enabled
        self._save_user_config()
        logger.info(f"Hume AI auto-upload {'enabled' if enabled else 'disabled'}")

    def set_memories_ai_auto_upload(self, enabled: bool) -> None:
        """Enable/disable Memories.ai auto-upload."""
        self._user_config["memories_ai_auto_upload"] = enabled
        self._save_user_config()
        logger.info(f"Memories.ai auto-upload {'enabled' if enabled else 'disabled'}")

    def _save_user_config(self) -> None:
        """Save user configuration to encrypted JSON file."""
        user_config_path = self.data_dir / "config.encrypted.json"
        try:
            with open(user_config_path, 'w') as f:
                json.dump(self._user_config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user config: {e}")

    # ========================================================================
    # Public API - Paths
    # ========================================================================
    
    def get_data_dir(self) -> Path:
        """Get data directory path."""
        return self.data_dir
    
    def get_sessions_dir(self) -> Path:
        """Get sessions directory path."""
        sessions_dir = self.data_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return sessions_dir
    
    def get_reports_dir(self) -> Path:
        """Get reports directory path."""
        reports_dir = self.data_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir
    
    def get_logs_dir(self) -> Path:
        """Get logs directory path."""
        logs_dir = self.data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir
    
    # ========================================================================
    # Public API - Save Configuration
    # ========================================================================
    
    def save_api_key(self, service: str, api_key: str) -> None:
        """
        Save API key in encrypted storage.
        
        Args:
            service: Service name (openai, hume, memories)
            api_key: Plain text API key
        """
        encrypted_key = self._encryption_key.encrypt(api_key.encode()).decode()
        key_name = f"{service}_api_key_encrypted"
        
        self._user_config[key_name] = encrypted_key
        
        # Save to file
        user_config_path = self.data_dir / "config.encrypted.json"
        with open(user_config_path, 'w') as f:
            json.dump(self._user_config, f, indent=2)
        
        logger.info(f"Saved encrypted API key for {service}")
    
    def save_developer_settings(self, settings: Dict[str, Any]) -> None:
        """
        Save developer settings to config.yaml.

        Args:
            settings: Dictionary of settings to save
        """
        # Validate settings before saving
        if not self._validate_config_structure(settings):
            logger.error("Cannot save invalid developer settings")
            return

        # Merge with existing developer config
        self._developer_config.update(settings)

        # Save to file
        dev_config_path = self.root_dir / "config.yaml"
        try:
            with open(dev_config_path, 'w') as f:
                yaml.dump(self._developer_config, f, default_flow_style=False)
            logger.info(f"Saved developer settings to {dev_config_path}")
        except Exception as e:
            logger.error(f"Failed to save developer settings: {e}")

    def get_config_health_status(self) -> Dict[str, Any]:
        """
        Get configuration health status and diagnostics.

        Returns:
            Dictionary with health information
        """
        return {
            "config_files": {
                "default_config": self._check_config_file_health(self.config_dir / "default_config.json"),
                "user_config": self._check_config_file_health(self.data_dir / "config.encrypted.json"),
                "developer_config": self._check_config_file_health(self.root_dir / "config.yaml")
            },
            "encryption_key": self._check_encryption_key_health(),
            "validation_status": {
                "default_config_valid": self._validate_config_structure(self._default_config),
                "user_config_valid": self._validate_config_structure(self._user_config),
                "developer_config_valid": self._validate_config_structure(self._developer_config),
                "merged_config_valid": self._validate_merged_config()
            },
            "file_sizes": {
                "default_config": self._get_config_file_size(self.config_dir / "default_config.json"),
                "user_config": self._get_config_file_size(self.data_dir / "config.encrypted.json"),
                "developer_config": self._get_config_file_size(self.root_dir / "config.yaml")
            }
        }

    def _check_config_file_health(self, file_path: Path) -> Dict[str, Any]:
        """Check health of a specific config file."""
        if not file_path.exists():
            return {"exists": False, "corrupted": False, "size": 0}

        try:
            # Try to read and parse the file
            if file_path.suffix == ".json":
                with open(file_path, 'r') as f:
                    json.load(f)
            elif file_path.suffix in [".yaml", ".yml"]:
                with open(file_path, 'r') as f:
                    yaml.safe_load(f)

            # Check file size (reasonable limits)
            size = file_path.stat().st_size
            if size > 1024 * 1024:  # 1MB limit
                return {"exists": True, "corrupted": True, "size": size, "issue": "file_too_large"}

            return {"exists": True, "corrupted": False, "size": size}

        except (json.JSONDecodeError, yaml.YAMLError) as e:
            return {"exists": True, "corrupted": True, "size": file_path.stat().st_size, "issue": str(e)}
        except Exception as e:
            return {"exists": True, "corrupted": True, "size": 0, "issue": f"read_error: {e}"}

    def _check_encryption_key_health(self) -> Dict[str, Any]:
        """Check encryption key health."""
        key_file = self.data_dir / ".encryption_key"

        if not key_file.exists():
            return {"exists": False, "valid": False}

        try:
            with open(key_file, 'rb') as f:
                key_data = f.read()

            if len(key_data) != 44:  # Fernet keys are 44 bytes
                return {"exists": True, "valid": False, "issue": "invalid_key_length"}

            # Try to create Fernet object
            Fernet(key_data)
            return {"exists": True, "valid": True}

        except Exception as e:
            return {"exists": True, "valid": False, "issue": str(e)}

    def _validate_merged_config(self) -> bool:
        """Validate the final merged configuration."""
        try:
            # Test some critical values
            interval = self.get_snapshot_interval_sec()
            bitrate_cam = self.get_video_bitrate_kbps_cam()
            bitrate_screen = self.get_video_bitrate_kbps_screen()
            max_uploads = self.get_max_parallel_uploads()

            return all([
                10 <= interval <= 300,
                100 <= bitrate_cam <= 5000,
                100 <= bitrate_screen <= 10000,
                1 <= max_uploads <= 10
            ])
        except Exception:
            return False

    def _get_config_file_size(self, file_path: Path) -> int:
        """Get size of config file in bytes."""
        try:
            return file_path.stat().st_size if file_path.exists() else 0
        except Exception:
            return 0

    def repair_config_file(self, file_type: str) -> bool:
        """
        Manually repair a specific config file.

        Args:
            file_type: "default", "user", or "developer"

        Returns:
            True if repair was successful
        """
        if file_type == "default":
            try:
                config_path = self.config_dir / "default_config.json"
                config_path.unlink(missing_ok=True)
                self._default_config = self._load_default_config()
                logger.info("Default config repaired successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to repair default config: {e}")
                return False

        elif file_type == "user":
            try:
                config_path = self.data_dir / "config.encrypted.json"
                config_path.unlink(missing_ok=True)
                self._user_config = {}
                logger.info("User config repaired successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to repair user config: {e}")
                return False

        elif file_type == "developer":
            try:
                config_path = self.root_dir / "config.yaml"
                config_path.unlink(missing_ok=True)
                self._developer_config = {}
                logger.info("Developer config repaired successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to repair developer config: {e}")
                return False

        return False
    
    # ========================================================================
    # Public API - Custom Prompts
    # ========================================================================
    
    def get_custom_prompt(self, prompt_type: str) -> Optional[str]:
        """
        Get custom AI prompt if defined.
        
        Args:
            prompt_type: Type of prompt (cam_snapshot, screen_snapshot, memories_analysis, comprehensive_report)
            
        Returns:
            Custom prompt text or None if using default
        """
        custom_prompts = self._user_config.get("custom_prompts", {})
        return custom_prompts.get(prompt_type)
    
    def save_custom_prompt(self, prompt_type: str, prompt_text: str) -> None:
        """
        Save custom AI prompt with versioning.
        
        Args:
            prompt_type: Type of prompt
            prompt_text: The custom prompt text
        """
        # Initialize custom_prompts if not exists
        if "custom_prompts" not in self._user_config:
            self._user_config["custom_prompts"] = {}
        
        # Archive old prompt version if exists
        if prompt_type in self._user_config["custom_prompts"]:
            self._archive_prompt_version(prompt_type, self._user_config["custom_prompts"][prompt_type])
        
        # Save new prompt
        self._user_config["custom_prompts"][prompt_type] = prompt_text
        self._save_user_config()
        
        logger.info(f"Custom prompt saved for {prompt_type} ({len(prompt_text)} chars)")
    
    def reset_prompt_to_default(self, prompt_type: str) -> None:
        """
        Reset prompt to default (remove custom prompt).
        
        Args:
            prompt_type: Type of prompt to reset
        """
        if "custom_prompts" in self._user_config:
            if prompt_type in self._user_config["custom_prompts"]:
                # Archive before deleting
                self._archive_prompt_version(prompt_type, self._user_config["custom_prompts"][prompt_type])
                
                del self._user_config["custom_prompts"][prompt_type]
                self._save_user_config()
                logger.info(f"Prompt reset to default for {prompt_type}")
    
    def _archive_prompt_version(self, prompt_type: str, prompt_text: str) -> None:
        """Archive old prompt version for history."""
        from datetime import datetime
        
        # Initialize prompt_versions if not exists
        if "prompt_versions" not in self._user_config:
            self._user_config["prompt_versions"] = []
        
        # Add version entry
        version_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": prompt_type,
            "prompt": prompt_text
        }
        
        self._user_config["prompt_versions"].append(version_entry)
        
        # Keep only last 10 versions per prompt type
        versions = self._user_config["prompt_versions"]
        type_versions = [v for v in versions if v["type"] == prompt_type]
        
        if len(type_versions) > 10:
            # Remove oldest versions beyond 10
            versions_to_keep = sorted(type_versions, key=lambda x: x["timestamp"], reverse=True)[:10]
            # Rebuild list keeping other prompt types and latest 10 of this type
            self._user_config["prompt_versions"] = [
                v for v in versions if v["type"] != prompt_type
            ] + versions_to_keep
        
        logger.info(f"Archived prompt version for {prompt_type}")
    
    def get_prompt_version_history(self, prompt_type: str) -> list:
        """Get version history for a prompt type."""
        versions = self._user_config.get("prompt_versions", [])
        return [v for v in versions if v["type"] == prompt_type]
    
    # ========================================================================
    # Public API - Label Profiles
    # ========================================================================
    
    def get_label_profiles_manager(self):
        """
        Get LabelProfileManager instance.
        
        Returns:
            LabelProfileManager for managing label profiles
        """
        from .label_profiles import LabelProfileManager
        
        profiles_path = self.config_dir / "label_profiles.yaml"
        return LabelProfileManager(profiles_path)
    
    def get_active_profile_name(self) -> str:
        """
        Get the last used/default label profile name.
        
        Returns:
            Profile name (defaults to "Default")
        """
        return str(self._get_config_value("active_label_profile", "Default"))
    
    def set_active_profile_name(self, profile_name: str) -> None:
        """
        Set the default label profile for new sessions.
        
        Args:
            profile_name: Profile name to use as default
        """
        self._user_config["active_label_profile"] = profile_name
        self._save_user_config()
        logger.info(f"Active label profile set to: {profile_name}")

