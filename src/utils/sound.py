from PyQt5.QtMultimedia import QSound
from pathlib import Path

class SoundManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.sound_enabled = self.config_manager.get_setting('alert_sound_enabled', True)
        
        # Define sound file path
        sound_path = Path(__file__).parent.parent.parent / 'resources' / 'alert.wav'
        self.alert_sound = str(sound_path)

    def play_alert(self):
        """Play alert sound if enabled"""
        if self.sound_enabled and Path(self.alert_sound).exists():
            QSound.play(self.alert_sound)

    def toggle_sound(self, enabled):
        """Toggle sound on/off"""
        self.sound_enabled = enabled
        self.config_manager.update_setting('alert_sound_enabled', enabled)