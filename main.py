import sys
from PyQt5.QtWidgets import QApplication
from src.core.model_service import ModelService
from src.core.video_service import VideoService
from src.ui.main_window import MainWindow

def main():
    # Initialize application
    app = QApplication(sys.argv)

    try:
        # Initialize services
        model_service = ModelService()
        video_service = VideoService(model_service.get_frame_sequence_size())

        # Create and show main window
        window = MainWindow(model_service, video_service)
        window.show()

        # Start event loop
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()