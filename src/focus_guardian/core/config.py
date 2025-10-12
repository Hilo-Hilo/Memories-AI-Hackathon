"""
Configuration management for Focus Guardian.

Implements a hierarchical configuration system:
1. config/default_config.json (version-controlled defaults)
2. data/config.encrypted.json (user overrides + encrypted API keys)
3. .env or config.yaml (developer settings)
4. Environment variables (highest priority)

Priority: ENV VARS > config.yaml > config.encrypted.json > default_config.json
"""

import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
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
                "data_retention_days": 30
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
        """Get snapshot interval in seconds (default: 60, min: 10)."""
        value = self._get_config_value("snapshot_interval_sec", 60)
        return max(10, int(value))  # Enforce minimum of 10 seconds
    
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
        # Merge with existing developer config
        self._developer_config.update(settings)
        
        # Save to file
        dev_config_path = self.root_dir / "config.yaml"
        with open(dev_config_path, 'w') as f:
            yaml.dump(self._developer_config, f, default_flow_style=False)
        
        logger.info(f"Saved developer settings to {dev_config_path}")

