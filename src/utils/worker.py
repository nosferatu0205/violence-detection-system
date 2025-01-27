from PyQt5.QtCore import QObject, pyqtSignal
import cv2
import time
from src.core.motion_detector import MotionDetector

class DetectionWorker(QObject):
    frame_ready = pyqtSignal(object)  # Emits processed frame
    prediction_ready = pyqtSignal(str, float)  # Emits (class, confidence)
    error = pyqtSignal(str)

    def __init__(self, video_service, model_service):
        super().__init__()
        self.video_service = video_service
        self.model_service = model_service
        self.motion_detector = MotionDetector()
        self.running = False
        self.is_violence = False

    def stop(self):
        self.running = False

    def run(self):
        """Main worker loop"""
        self.running = True
        
        try:
            while self.running:
                # Get frame
                frame = self.video_service.get_frame()
                if frame is None:
                    break

                # Detect motion
                motion_regions = self.motion_detector.detect_motion(frame)
                
                # Add visual indicators
                if motion_regions:
                    frame = self.motion_detector.draw_motion_regions(
                        frame, motion_regions, self.is_violence)

                # Emit frame for display
                self.frame_ready.emit(frame)

                # Run detection if we have enough frames
                frames = self.video_service.get_frame_sequence()
                if frames is not None:
                    try:
                        predicted_class, confidence = self.model_service.predict_frames(frames)
                        self.is_violence = predicted_class == "Violence" and confidence > 0.5
                        self.prediction_ready.emit(predicted_class, confidence)
                    except Exception as e:
                        self.error.emit(f"Detection error: {str(e)}")

                # Small sleep to prevent excessive CPU usage
                time.sleep(0.01)

        except Exception as e:
            self.error.emit(f"Worker error: {str(e)}")
        
        self.running = False