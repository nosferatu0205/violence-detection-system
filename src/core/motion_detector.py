import cv2
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