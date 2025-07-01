"""Configuration management for the voice assistant application."""

import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the voice assistant."""
    
    DEFAULT_CONFIG = {
        "hotkey": "f9",
        "whisper_model": "small.en",
        "ollama_model": "llama3:latest",
        "ollama_host": "localhost",
        "ollama_port": 11434,
        "audio_device_index": None,
        "audio_sample_rate": 16000,
        "audio_chunk_size": 1024,
        "log_transcriptions": True,
        "log_file": "logs/transcriptions.log",
        "notification_enabled": True,
        "copy_to_clipboard": True,
        "gui_theme": "dark",
        "auto_typing_enabled": False,
        "auto_typing_delay": 1.0,
        "auto_typing_speed": 0.02,
        "auto_typing_mode": "raw",  # "raw", "corrected", or "both"
        "auto_typing_excluded_apps": ["Keychain Access", "Login Window", "1Password"],
        "confidence_threshold": -0.5,  # Minimum confidence for accepting transcriptions
        "silence_skip_threshold": 50,  # Skip Whisper processing if max amplitude below this value
        "start_at_login": False,  # Start application at system login
        "start_minimized": True  # Start minimized to system tray when launched at login
    }
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        import sys
        
        # Handle bundled app read-only filesystem issue
        if getattr(sys, 'frozen', False):
            # Running as bundled app - use user's home directory for config
            import os.path
            config_dir = os.path.expanduser("~/.speechy")
            os.makedirs(config_dir, exist_ok=True)
            self.config_file = os.path.join(config_dir, "config.json")
            logger.info(f"Using bundled app config location: {self.config_file}")
        else:
            self.config_file = config_file
        
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file or create default if not exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                self.config = {**self.DEFAULT_CONFIG, **loaded_config}
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.config = self.DEFAULT_CONFIG.copy()
                self.save_config()
                logger.info(f"Default configuration created at {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        self.save_config()
    
    def get_hotkey(self) -> str:
        """Get hotkey setting."""
        return self.config.get("hotkey", "f9")
    
    def get_whisper_model(self) -> str:
        """Get Whisper model setting."""
        return self.config.get("whisper_model", "base")
    
    def get_ollama_model(self) -> str:
        """Get Ollama model setting."""
        return self.config.get("ollama_model", "llama3.2:3b")
    
    def get_ollama_url(self) -> str:
        """Get Ollama API URL."""
        host = self.config.get("ollama_host", "localhost")
        port = self.config.get("ollama_port", 11434)
        return f"http://{host}:{port}"
    
    def get_audio_device_index(self) -> Optional[int]:
        """Get audio device index."""
        return self.config.get("audio_device_index")
    
    def get_audio_sample_rate(self) -> int:
        """Get audio sample rate."""
        return self.config.get("audio_sample_rate", 16000)
    
    def get_audio_chunk_size(self) -> int:
        """Get audio chunk size."""
        return self.config.get("audio_chunk_size", 1024)
    
    def should_log_transcriptions(self) -> bool:
        """Check if transcriptions should be logged."""
        return self.config.get("log_transcriptions", True)
    
    def get_log_file(self) -> str:
        """Get log file path."""
        return self.config.get("log_file", "logs/transcriptions.log")
    
    def is_notification_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.config.get("notification_enabled", True)
    
    def should_copy_to_clipboard(self) -> bool:
        """Check if text should be copied to clipboard."""
        return self.config.get("copy_to_clipboard", True)
    
    def get_gui_theme(self) -> str:
        """Get GUI theme."""
        return self.config.get("gui_theme", "dark")
    
    def is_auto_typing_enabled(self) -> bool:
        """Check if auto-typing is enabled."""
        return self.config.get("auto_typing_enabled", False)
    
    def get_auto_typing_delay(self) -> float:
        """Get auto-typing delay."""
        return self.config.get("auto_typing_delay", 1.0)
    
    def get_auto_typing_speed(self) -> float:
        """Get auto-typing speed."""
        return self.config.get("auto_typing_speed", 0.02)
    
    def get_auto_typing_mode(self) -> str:
        """Get auto-typing mode."""
        return self.config.get("auto_typing_mode", "raw")
    
    def get_auto_typing_excluded_apps(self) -> list:
        """Get list of excluded applications for auto-typing."""
        return self.config.get("auto_typing_excluded_apps", ["Keychain Access", "Login Window", "1Password"])
    
    def get_confidence_threshold(self) -> float:
        """Get confidence threshold for accepting transcriptions."""
        return self.config.get("confidence_threshold", -0.5)
    
    def get_silence_skip_threshold(self) -> int:
        """Get silence skip threshold for audio processing."""
        return self.config.get("silence_skip_threshold", 50)
    
    def should_start_at_login(self) -> bool:
        """Check if application should start at login."""
        return self.config.get("start_at_login", False)
    
    def should_start_minimized(self) -> bool:
        """Check if application should start minimized."""
        return self.config.get("start_minimized", True)