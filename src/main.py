import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from src.core.model_service import ModelService
from src.core.video_service import VideoService
from src.ui.main_window import MainWindow
from src.utils.config import ConfigManager
from src.utils.sound import SoundManager

def main():
    # Initialize application
    app = QApplication(sys.argv)

    try:
        # Initialize configuration
        config_manager = ConfigManager()

        # Initialize services
        model_service = ModelService(config_manager)
        video_service = VideoService(config_manager, model_service.get_frame_sequence_size())
        sound_manager = SoundManager(config_manager)

        # Create and show main window
        window = MainWindow(model_service, video_service, config_manager, sound_manager)
        window.show()

        # Start event loop
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()