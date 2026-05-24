"""
PhoenixDrive Configuration Management
Handles application settings and preferences
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration."""
    
    # API settings
    api_url: str = "http://localhost:3000"
    api_timeout: int = 30
    
    # UI settings
    theme: str = "dark"
    window_width: int = 1200
    window_height: int = 800
    remember_window_size: bool = True
    
    # Build settings
    auto_verify: bool = True
    dry_run_default: bool = False
    parallel_builds: int = 2
    
    # Storage settings
    cache_dir: str = ""
    downloads_dir: str = ""
    keep_cache: bool = True
    max_cache_size_gb: int = 10
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = ""
    
    # Advanced settings
    enable_analytics: bool = True
    check_updates: bool = True
    auto_update: bool = False
    
    # Notification settings
    show_notifications: bool = True
    sound_enabled: bool = True
    
    def __post_init__(self):
        """Initialize default paths if not set."""
        if not self.cache_dir:
            self.cache_dir = str(Path.home() / ".phoenixdrive" / "cache")
        if not self.downloads_dir:
            self.downloads_dir = str(Path.home() / "Downloads")
        if not self.log_file:
            self.log_file = str(Path.home() / ".phoenixdrive" / "logs" / "phoenixdrive.log")


class Config:
    """Configuration manager."""
    
    CONFIG_DIR = Path.home() / ".phoenixdrive"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = self.CONFIG_DIR
        self.config_file = self.CONFIG_FILE
        self.config = self._load_config()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create other directories
        cache_dir = Path(self.config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        log_dir = Path(self.config.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return AppConfig(**data)
            except Exception as e:
                logger.error(f"Failed to load config: {e}, using defaults")
                return AppConfig()
        else:
            return AppConfig()
    
    def save(self):
        """Save configuration to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        try:
            parts = key.split('.')
            value = self.config
            for part in parts:
                value = getattr(value, part)
            return value
        except (AttributeError, KeyError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        try:
            parts = key.split('.')
            obj = self.config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
            self.save()
        except Exception as e:
            logger.error(f"Failed to set config {key}: {e}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = AppConfig()
        self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self.config)
    
    def from_dict(self, data: Dict[str, Any]):
        """Load configuration from dictionary."""
        try:
            self.config = AppConfig(**data)
            self.save()
        except Exception as e:
            logger.error(f"Failed to load config from dict: {e}")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
