from PyQt5.QtCore import QObject, pyqtSignal
import cv2
import time
import numpy as np

class MotionDetector:
    def __init__(self):
        self.previous_frame = None
        self.min_area = 1000  # Increased minimum area to reduce sensitivity
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=50, varThreshold=32, detectShadows=False)  # Increased threshold

    def detect_motion(self, frame):
        """Detect motion in frame and return regions of interest"""
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.erode(fg_mask, kernel, iterations=2)  # More erosion
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=3)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and get bounding boxes
        motion_regions = []
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                motion_regions.append((x, y, w, h))
        
        # Merge overlapping boxes
        return self.merge_boxes(motion_regions)

    def merge_boxes(self, boxes):
        """Merge overlapping bounding boxes"""
        if not boxes:
            return []

        # Convert to a format suitable for NMS
        boxes_array = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        
        # Calculate areas
        areas = (boxes_array[:, 2] - boxes_array[:, 0]) * (boxes_array[:, 3] - boxes_array[:, 1])
        
        # Sort boxes by area
        idxs = areas.argsort()
        
        # Initialize pick list
        pick = []
        
        while len(idxs) > 0:
            # Grab the last box (largest area)
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            
            # Find the overlap with remaining boxes
            xx1 = np.maximum(boxes_array[i, 0], boxes_array[idxs[:last], 0])
            yy1 = np.maximum(boxes_array[i, 1], boxes_array[idxs[:last], 1])
            xx2 = np.minimum(boxes_array[i, 2], boxes_array[idxs[:last], 2])
            yy2 = np.minimum(boxes_array[i, 3], boxes_array[idxs[:last], 3])
            
            # Calculate overlap area
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            overlap = (w * h) / areas[idxs[:last]]
            
            # Delete all indexes from the index list that exceed the overlap threshold
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > 0.3)[0])))
        
        # Convert back to (x, y, w, h) format
        merged_boxes = []
        for i in pick:
            x1, y1, x2, y2 = boxes_array[i]
            merged_boxes.append((int(x1), int(y1), int(x2 - x1), int(y2 - y1)))
        
        return merged_boxes

    def draw_motion_regions(self, frame, regions, is_violence=False):
        """Draw motion regions on frame"""
        color = (0, 0, 255) if is_violence else (0, 255, 0)
        frame_copy = frame.copy()
        
        # Draw only the outlines without fill
        for x, y, w, h in regions:
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), color, 2)
        
        return frame_copy

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
        self.violence_persist_time = None
        self.VIOLENCE_PERSISTENCE = 3  # 3 seconds persistence
        self.manual_violence_trigger = False
        
    def setShowBoxes(self, show):
        """Toggle bounding box display"""
        self.show_boxes = show
        
    def trigger_manual_violence(self):
        """Manually trigger violence detection"""
        self.is_violence = True
        self.manual_violence_trigger = True
        self.violence_persist_time = time.time()
        
    def trigger_manual_nonviolence(self): 
        self.is_violence = False
        self.manual_violence_trigger = False
        self.violence_persist_time = time.time()  # Used to keep nonviolence state for 1 second
        
    def stop(self):
        """Stop the worker"""
        self.running = False
        
    def run(self):
        """Main worker loop"""
        self.running = True
        predicted_class = "NonViolence"  # Default value
        confidence = 0.0  # Default value
        
        try:
            while self.running:
                # Get frame
                frame = self.video_service.get_frame()
                if frame is None:
                    break

                current_time = time.time()
                
                # Check for manual triggers and persistence
                if self.manual_violence_trigger or (
                    self.violence_persist_time and 
                    current_time - self.violence_persist_time < (
                        3 if self.is_violence else 1  # 3 seconds for violence, 1 for nonviolence
                    )
                ):
                    predicted_class = "Violence" if self.is_violence else "NonViolence"
                    confidence = 1.0
                else:
                    # Run detection if we have enough frames
                    frames = self.video_service.get_frame_sequence()
                    if frames is not None:
                        try:
                            predicted_class, confidence = self.model_service.predict_frames(frames)
                            if predicted_class == "Violence" and confidence > 0.5:
                                self.is_violence = True
                                self.violence_persist_time = current_time
                            elif not self.violence_persist_time or (
                                current_time - self.violence_persist_time >= self.VIOLENCE_PERSISTENCE):
                                self.is_violence = False
                                self.manual_violence_trigger = False
                        except Exception as e:
                            self.error.emit(f"Detection error: {str(e)}")
                            continue

                # Detect motion and update display
                motion_regions = self.motion_detector.detect_motion(frame)
                frame_to_display = frame.copy()
                if motion_regions and self.show_boxes:
                    frame_to_display = self.motion_detector.draw_motion_regions(
                        frame_to_display, motion_regions, self.is_violence)

                self.frame_ready.emit(frame_to_display)
                self.prediction_ready.emit(predicted_class, confidence)

                time.sleep(0.01)

        except Exception as e:
            self.error.emit(f"Worker error: {str(e)}")
        
        self.running = False