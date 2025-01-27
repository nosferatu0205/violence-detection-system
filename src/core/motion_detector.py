import cv2
import numpy as np

class MotionDetector:
    def __init__(self):
        self.previous_frame = None
        self.min_area = 500  # Minimum area to consider as motion
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=50, varThreshold=16, detectShadows=False)

    def detect_motion(self, frame):
        """Detect motion in frame and return regions of interest"""
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.erode(fg_mask, kernel, iterations=1)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and get bounding boxes
        motion_regions = []
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                motion_regions.append((x, y, w, h))
        
        return motion_regions

    def draw_motion_regions(self, frame, regions, is_violence=False):
        """Draw motion regions on frame"""
        color = (0, 0, 255) if is_violence else (0, 255, 0)
        frame_copy = frame.copy()
        
        for x, y, w, h in regions:
            # Draw rectangle around motion region
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), color, 2)
            
            # Add semi-transparent overlay
            overlay = frame_copy.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
            frame_copy = cv2.addWeighted(overlay, 0.2, frame_copy, 0.8, 0)
            
        return frame_copy