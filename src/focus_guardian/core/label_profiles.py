"""
Label profile management for customizable detection labels.

Allows users to create custom label sets for different session types,
stored in YAML configuration with validation and UI management.
"""

import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LabelDefinition:
    """Definition for a single detection label."""
    name: str
    category: str  # distraction | focus | absence | borderline | neutral
    threshold: float  # 0.0 - 1.0
    description: str


@dataclass
class LabelProfile:
    """Complete label profile for a session type."""
    name: str
    description: str
    cam_labels: Dict[str, LabelDefinition]  # {label_name: definition}
    screen_labels: Dict[str, LabelDefinition]
    
    def get_cam_label_names(self) -> Set[str]:
        """Get set of all camera label names."""
        return set(self.cam_labels.keys())
    
    def get_screen_label_names(self) -> Set[str]:
        """Get set of all screen label names."""
        return set(self.screen_labels.keys())
    
    def get_cam_labels_by_category(self, category: str) -> Set[str]:
        """Get camera labels for a specific category."""
        return {
            name for name, label in self.cam_labels.items()
            if label.category == category
        }
    
    def get_screen_labels_by_category(self, category: str) -> Set[str]:
        """Get screen labels for a specific category."""
        return {
            name for name, label in self.screen_labels.items()
            if label.category == category
        }
    
    def get_cam_thresholds(self) -> Dict[str, float]:
        """Get confidence thresholds for camera labels."""
        return {name: label.threshold for name, label in self.cam_labels.items()}
    
    def get_screen_thresholds(self) -> Dict[str, float]:
        """Get confidence thresholds for screen labels."""
        return {name: label.threshold for name, label in self.screen_labels.items()}


class LabelProfileManager:
    """Manages label profiles from YAML configuration."""
    
    VALID_CATEGORIES = {"distraction", "focus", "absence", "borderline", "neutral"}
    
    def __init__(self, config_path: Path):
        """
        Initialize label profile manager.
        
        Args:
            config_path: Path to label_profiles.yaml
        """
        self.config_path = config_path
        self._profiles: Dict[str, LabelProfile] = {}
        
        # Ensure config file exists
        if not self.config_path.exists():
            logger.warning(f"Label profiles config not found: {config_path}")
            self._create_default_config()
        
        # Load profiles
        self._load_profiles()
        
        logger.info(f"Label profile manager initialized with {len(self._profiles)} profiles")
    
    def _create_default_config(self) -> None:
        """Create default label_profiles.yaml from hardcoded labels."""
        logger.info("Creating default label profiles config...")
        
        # Import hardcoded labels as fallback
        from ..core.models import (
            CAM_LABELS, SCREEN_LABELS,
            CAM_DISTRACTION_LABELS, CAM_FOCUS_LABELS, CAM_ABSENCE_LABELS,
            SCREEN_DISTRACTION_LABELS, SCREEN_FOCUS_LABELS,
            SCREEN_BORDERLINE_LABELS, SCREEN_NEUTRAL_LABELS,
            CONFIDENCE_THRESHOLDS
        )
        
        # This should already exist from the YAML file we created
        # But if somehow it doesn't exist, we log a warning
        logger.warning("Label profiles YAML should exist - check config/label_profiles.yaml")
    
    def _load_profiles(self) -> None:
        """Load all profiles from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'profiles' not in data:
                raise ValueError("Invalid YAML structure: missing 'profiles' key")
            
            profiles_data = data['profiles']
            
            for profile_name, profile_config in profiles_data.items():
                try:
                    profile = self._parse_profile(profile_name, profile_config)
                    self._profiles[profile_name] = profile
                    logger.debug(f"Loaded profile: {profile_name}")
                except Exception as e:
                    logger.error(f"Failed to parse profile '{profile_name}': {e}")
            
            logger.info(f"Loaded {len(self._profiles)} label profiles")
            
        except Exception as e:
            logger.error(f"Failed to load label profiles: {e}", exc_info=True)
            # Create minimal Default profile as fallback
            self._create_fallback_profile()
    
    def _parse_profile(self, name: str, config: Dict) -> LabelProfile:
        """Parse profile from YAML config."""
        description = config.get('description', '')
        
        # Parse camera labels
        cam_labels = {}
        for label_name, label_data in config.get('cam_labels', {}).items():
            cam_labels[label_name] = LabelDefinition(
                name=label_name,
                category=label_data['category'],
                threshold=float(label_data['threshold']),
                description=label_data.get('description', '')
            )
        
        # Parse screen labels
        screen_labels = {}
        for label_name, label_data in config.get('screen_labels', {}).items():
            screen_labels[label_name] = LabelDefinition(
                name=label_name,
                category=label_data['category'],
                threshold=float(label_data['threshold']),
                description=label_data.get('description', '')
            )
        
        return LabelProfile(
            name=name,
            description=description,
            cam_labels=cam_labels,
            screen_labels=screen_labels
        )
    
    def _create_fallback_profile(self) -> None:
        """Create minimal fallback profile if loading fails."""
        logger.warning("Creating fallback Default profile from hardcoded labels")
        
        from ..core.models import (
            CAM_DISTRACTION_LABELS, CAM_FOCUS_LABELS, CAM_ABSENCE_LABELS,
            SCREEN_DISTRACTION_LABELS, SCREEN_FOCUS_LABELS,
            CONFIDENCE_THRESHOLDS
        )
        
        cam_labels = {}
        for label in CAM_DISTRACTION_LABELS:
            cam_labels[label] = LabelDefinition(
                name=label,
                category="distraction",
                threshold=CONFIDENCE_THRESHOLDS.get(label, 0.7),
                description=f"{label} (fallback)"
            )
        for label in CAM_FOCUS_LABELS:
            cam_labels[label] = LabelDefinition(
                name=label,
                category="focus",
                threshold=CONFIDENCE_THRESHOLDS.get(label, 0.6),
                description=f"{label} (fallback)"
            )
        for label in CAM_ABSENCE_LABELS:
            cam_labels[label] = LabelDefinition(
                name=label,
                category="absence",
                threshold=CONFIDENCE_THRESHOLDS.get(label, 0.8),
                description=f"{label} (fallback)"
            )
        
        screen_labels = {}
        for label in SCREEN_DISTRACTION_LABELS:
            screen_labels[label] = LabelDefinition(
                name=label,
                category="distraction",
                threshold=CONFIDENCE_THRESHOLDS.get(label, 0.7),
                description=f"{label} (fallback)"
            )
        for label in SCREEN_FOCUS_LABELS:
            screen_labels[label] = LabelDefinition(
                name=label,
                category="focus",
                threshold=CONFIDENCE_THRESHOLDS.get(label, 0.7),
                description=f"{label} (fallback)"
            )
        
        self._profiles["Default"] = LabelProfile(
            name="Default",
            description="Fallback profile from hardcoded labels",
            cam_labels=cam_labels,
            screen_labels=screen_labels
        )
    
    def get_profile(self, name: str) -> Optional[LabelProfile]:
        """Get profile by name."""
        return self._profiles.get(name)
    
    def list_profiles(self) -> List[str]:
        """Get list of all profile names."""
        return list(self._profiles.keys())
    
    def profile_exists(self, name: str) -> bool:
        """Check if profile exists."""
        return name in self._profiles
    
    def create_profile(
        self,
        name: str,
        description: str,
        clone_from: Optional[str] = None
    ) -> LabelProfile:
        """
        Create new profile.
        
        Args:
            name: Profile name
            description: Profile description
            clone_from: Optional profile name to clone from
            
        Returns:
            New LabelProfile instance
        """
        if name in self._profiles:
            raise ValueError(f"Profile '{name}' already exists")
        
        if clone_from:
            source = self._profiles.get(clone_from)
            if not source:
                raise ValueError(f"Source profile '{clone_from}' not found")
            
            # Deep copy labels
            cam_labels = {
                k: LabelDefinition(v.name, v.category, v.threshold, v.description)
                for k, v in source.cam_labels.items()
            }
            screen_labels = {
                k: LabelDefinition(v.name, v.category, v.threshold, v.description)
                for k, v in source.screen_labels.items()
            }
        else:
            cam_labels = {}
            screen_labels = {}
        
        profile = LabelProfile(
            name=name,
            description=description,
            cam_labels=cam_labels,
            screen_labels=screen_labels
        )
        
        self._profiles[name] = profile
        self._save_profiles()
        
        logger.info(f"Created new profile: {name}")
        return profile
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete profile (cannot delete Default).
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if deleted, False if can't delete
        """
        if name == "Default":
            logger.warning("Cannot delete Default profile")
            return False
        
        if name not in self._profiles:
            logger.warning(f"Profile '{name}' not found")
            return False
        
        del self._profiles[name]
        self._save_profiles()
        
        logger.info(f"Deleted profile: {name}")
        return True
    
    def update_profile(self, profile: LabelProfile) -> None:
        """
        Update existing profile.
        
        Args:
            profile: Updated LabelProfile instance
        """
        if profile.name not in self._profiles:
            raise ValueError(f"Profile '{profile.name}' not found")
        
        # Validate profile before saving
        self.validate_profile(profile)
        
        self._profiles[profile.name] = profile
        self._save_profiles()
        
        logger.info(f"Updated profile: {profile.name}")
    
    def add_label_to_profile(
        self,
        profile_name: str,
        label_type: str,  # "cam" or "screen"
        label_def: LabelDefinition
    ) -> None:
        """
        Add label to profile.
        
        Args:
            profile_name: Profile to modify
            label_type: "cam" or "screen"
            label_def: Label definition to add
        """
        profile = self._profiles.get(profile_name)
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found")
        
        # Validate category
        if label_def.category not in self.VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{label_def.category}'. "
                f"Must be one of: {', '.join(self.VALID_CATEGORIES)}"
            )
        
        # Validate threshold
        if not (0.0 <= label_def.threshold <= 1.0):
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {label_def.threshold}")
        
        # Add to appropriate label set
        if label_type == "cam":
            if label_def.name in profile.cam_labels:
                raise ValueError(f"Camera label '{label_def.name}' already exists in profile")
            profile.cam_labels[label_def.name] = label_def
        elif label_type == "screen":
            if label_def.name in profile.screen_labels:
                raise ValueError(f"Screen label '{label_def.name}' already exists in profile")
            profile.screen_labels[label_def.name] = label_def
        else:
            raise ValueError(f"Invalid label_type '{label_type}', must be 'cam' or 'screen'")
        
        self._save_profiles()
        logger.info(f"Added {label_type} label '{label_def.name}' to profile '{profile_name}'")
    
    def remove_label_from_profile(
        self,
        profile_name: str,
        label_type: str,
        label_name: str
    ) -> None:
        """Remove label from profile."""
        profile = self._profiles.get(profile_name)
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found")
        
        if label_type == "cam":
            if label_name not in profile.cam_labels:
                raise ValueError(f"Camera label '{label_name}' not found in profile")
            del profile.cam_labels[label_name]
        elif label_type == "screen":
            if label_name not in profile.screen_labels:
                raise ValueError(f"Screen label '{label_name}' not found in profile")
            del profile.screen_labels[label_name]
        else:
            raise ValueError(f"Invalid label_type '{label_type}'")
        
        self._save_profiles()
        logger.info(f"Removed {label_type} label '{label_name}' from profile '{profile_name}'")
    
    def validate_profile(self, profile: LabelProfile) -> bool:
        """
        Validate profile structure and content.
        
        Args:
            profile: Profile to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        # Check that profile has at least some labels
        if not profile.cam_labels and not profile.screen_labels:
            raise ValueError("Profile must have at least one label")
        
        # Validate camera labels
        for label_name, label_def in profile.cam_labels.items():
            if label_def.category not in self.VALID_CATEGORIES:
                raise ValueError(
                    f"Invalid category '{label_def.category}' for label '{label_name}'"
                )
            if not (0.0 <= label_def.threshold <= 1.0):
                raise ValueError(
                    f"Invalid threshold {label_def.threshold} for label '{label_name}'"
                )
        
        # Validate screen labels
        for label_name, label_def in profile.screen_labels.items():
            if label_def.category not in self.VALID_CATEGORIES:
                raise ValueError(
                    f"Invalid category '{label_def.category}' for label '{label_name}'"
                )
            if not (0.0 <= label_def.threshold <= 1.0):
                raise ValueError(
                    f"Invalid threshold {label_def.threshold} for label '{label_name}'"
                )
        
        # Warn if no distraction labels (won't detect distractions)
        cam_distraction_count = len(profile.get_cam_labels_by_category("distraction"))
        screen_distraction_count = len(profile.get_screen_labels_by_category("distraction"))
        
        if cam_distraction_count == 0 and screen_distraction_count == 0:
            logger.warning(
                f"Profile '{profile.name}' has no distraction labels - "
                "won't detect distractions"
            )
        
        return True
    
    def _save_profiles(self) -> None:
        """Save all profiles to YAML file."""
        try:
            # Backup existing file
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(
                    f'.yaml.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                )
                shutil.copy2(self.config_path, backup_path)
                logger.debug(f"Backed up profiles to {backup_path}")
            
            # Convert profiles to YAML structure
            yaml_data = {'profiles': {}}
            
            for profile_name, profile in self._profiles.items():
                yaml_data['profiles'][profile_name] = {
                    'description': profile.description,
                    'cam_labels': {},
                    'screen_labels': {}
                }
                
                # Convert camera labels
                for label_name, label_def in profile.cam_labels.items():
                    yaml_data['profiles'][profile_name]['cam_labels'][label_name] = {
                        'category': label_def.category,
                        'threshold': label_def.threshold,
                        'description': label_def.description
                    }
                
                # Convert screen labels
                for label_name, label_def in profile.screen_labels.items():
                    yaml_data['profiles'][profile_name]['screen_labels'][label_name] = {
                        'category': label_def.category,
                        'threshold': label_def.threshold,
                        'description': label_def.description
                    }
            
            # Write to file
            with open(self.config_path, 'w') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved {len(self._profiles)} profiles to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}", exc_info=True)
            raise
    
    def get_all_profiles(self) -> Dict[str, LabelProfile]:
        """Get all loaded profiles."""
        return self._profiles.copy()
    
    def reload_profiles(self) -> None:
        """Reload profiles from YAML file."""
        self._profiles.clear()
        self._load_profiles()
        logger.info("Profiles reloaded from disk")

