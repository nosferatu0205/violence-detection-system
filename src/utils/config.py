import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    'performance_mode': 1,  # 0: Performance, 1: Balanced, 2: Quality
    'confidence_threshold': 0.5,
    'last_source': 'Camera',
    'camera_index': 0,
    'alert_sound_enabled': True,
    'processing_settings': {
        'performance': {
            'frame_skip': 2,
            'resize_factor': 0.5
        },
        'balanced': {
            'frame_skip': 1,
            'resize_factor': 0.75
        },
        'quality': {
            'frame_skip': 0,
            'resize_factor': 1.0
        }
    }
}

class ConfigManager:
    def __init__(self, config_path='config.json'):
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Update with any missing default values
                    return self._update_with_defaults(loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def _update_with_defaults(self, config):
        """Recursively update config with any missing default values"""
        updated = config.copy()
        for key, value in DEFAULT_CONFIG.items():
            if key not in updated:
                updated[key] = value
            elif isinstance(value, dict) and isinstance(updated[key], dict):
                updated[key] = self._update_with_defaults(updated[key])
        return updated

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_processing_settings(self, mode=None):
        """Get processing settings for current or specified mode"""
        if mode is None:
            mode = self.config['performance_mode']
        
        mode_map = {0: 'performance', 1: 'balanced', 2: 'quality'}
        return self.config['processing_settings'][mode_map[mode]]

    def update_setting(self, key, value):
        """Update a configuration setting"""
        if key in self.config:
            self.config[key] = value
            self.save_config()

    def get_setting(self, key, default=None):
        """Get a configuration setting"""
        return self.config.get(key, default)