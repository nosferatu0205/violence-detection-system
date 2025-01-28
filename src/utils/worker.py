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
        self.show_boxes = True
        # Add smoothing variables
        self.violence_counter = 0
        self.cooldown_counter = 0
        self.MIN_VIOLENCE_FRAMES = 15
        self.COOLDOWN_PERIOD = 45

    def stop(self):
        self.running = False

    def set_show_boxes(self, show):
        """Toggle bounding box display"""
        self.show_boxes = show

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
                
                # Add visual indicators if enabled
                frame_to_display = frame.copy()
                if motion_regions and self.show_boxes:
                    frame_to_display = self.motion_detector.draw_motion_regions(
                        frame_to_display, motion_regions, self.is_violence)

                # Emit frame for display
                self.frame_ready.emit(frame_to_display)

                # Run detection if we have enough frames
                frames = self.video_service.get_frame_sequence()
                if frames is not None:
                    try:
                        predicted_class, confidence = self.model_service.predict_frames(frames)
                        
                        # Apply smoothing logic
                        if predicted_class == "Violence" and confidence > 0.65:
                            self.violence_counter += 1
                            if self.violence_counter >= self.MIN_VIOLENCE_FRAMES:
                                self.is_violence = True
                                self.cooldown_counter = 0
                        elif self.is_violence:
                            self.cooldown_counter += 1
                            if self.cooldown_counter >= self.COOLDOWN_PERIOD:
                                self.is_violence = False
                                self.violence_counter = 0
                        else:
                            self.violence_counter = max(0, self.violence_counter - 1)

                        # Use smoothed state for prediction
                        if self.is_violence:
                            self.prediction_ready.emit("Violence", max(confidence, 0.65))
                        else:
                            self.prediction_ready.emit(predicted_class, confidence)
                            
                    except Exception as e:
                        self.error.emit(f"Detection error: {str(e)}")

                # Small sleep to prevent excessive CPU usage
                time.sleep(0.01)

        except Exception as e:
            self.error.emit(f"Worker error: {str(e)}")
        
        self.running = False