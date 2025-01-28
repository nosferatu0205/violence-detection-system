import cv2
import numpy as np

import cv2
import numpy as np

class MotionDetector:
    def __init__(self):
        self.previous_frame = None
        self.min_area = 1000  # Increased minimum area to reduce sensitivity
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
<<<<<<< HEAD
<<<<<<< HEAD
            history=20,  # Reduced history
            varThreshold=32, 
            detectShadows=False)
        self.frame_count = 0
        self.process_interval = 2  # Process every nth frame

    def detect_motion(self, frame):
        """Detect motion in frame and return regions of interest"""
        self.frame_count += 1
        
        # Only process every nth frame
        if self.frame_count % self.process_interval != 0:
            return self.previous_frame if self.previous_frame else []

        # Downsample frame for faster processing
        frame_small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame_small)
        
        # Simple noise removal
        fg_mask = cv2.medianBlur(fg_mask, 3)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and scale back bounding boxes
        motion_regions = []
        min_area_small = self.min_area / 4  # Adjust for downscaled image
=======
            history=50, varThreshold=32, detectShadows=False)  # Increased threshold

    def detect_motion(self, frame):
        """Detect motion in frame and return regions of interest"""
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)
>>>>>>> parent of b4e113e (broken code, does not work right now)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.erode(fg_mask, kernel, iterations=2)  # More erosion
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=3)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and get bounding boxes
        motion_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area_small:
                x, y, w, h = cv2.boundingRect(contour)
<<<<<<< HEAD
                # Scale back to original size
                motion_regions.append((x*2, y*2, w*2, h*2))
        
        # Merge overlapping boxes
        merged_boxes = self.merge_boxes(motion_regions)
        self.previous_frame = merged_boxes
        return merged_boxes
=======
                motion_regions.append((x, y, w, h))
        
        # Merge overlapping boxes
        return self.merge_boxes(motion_regions)
>>>>>>> parent of b4e113e (broken code, does not work right now)

=======
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

>>>>>>> parent of b4e113e (broken code, does not work right now)
    def merge_boxes(self, boxes):
        """Merge overlapping bounding boxes"""
        if not boxes:
            return []

<<<<<<< HEAD
<<<<<<< HEAD
        boxes_array = np.array([[x, y, x + w, y + h] for (x, y, w, h) in boxes])
        pick = []
        
        if len(boxes_array) == 0:
            return []

        x1 = boxes_array[:, 0]
        y1 = boxes_array[:, 1]
        x2 = boxes_array[:, 2]
        y2 = boxes_array[:, 3]

        area = (x2 - x1) * (y2 - y1)
        idxs = np.argsort(area)

        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)

            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])

            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            
            overlap = (w * h) / area[idxs[:last]]
            
            idxs = np.delete(idxs, np.concatenate(([last],
                np.where(overlap > 0.3)[0])))

        merged_boxes = []
        for i in pick:
            merged_boxes.append((
                int(x1[i]), int(y1[i]),
                int(x2[i] - x1[i]), int(y2[i] - y1[i])
            ))
=======
=======
>>>>>>> parent of b4e113e (broken code, does not work right now)
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
<<<<<<< HEAD
>>>>>>> parent of b4e113e (broken code, does not work right now)
=======
>>>>>>> parent of b4e113e (broken code, does not work right now)
        
        return merged_boxes

    def draw_motion_regions(self, frame, regions, is_violence=False):
        """Draw motion regions on frame"""
        color = (0, 0, 255) if is_violence else (0, 255, 0)
        frame_copy = frame.copy()
        
        # Draw only the outlines without fill
        for x, y, w, h in regions:
            cv2.rectangle(frame_copy, (x, y), (x + w, y + h), color, 2)
        
        return frame_copy