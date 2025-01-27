import cv2
from collections import deque
import numpy as np

class VideoService:
    def __init__(self, sequence_length):
        """Initialize video service"""
        self.cap = None
        self.sequence_length = sequence_length
        self.frames_queue = deque(maxlen=sequence_length)

    def start_video_capture(self, source):
        """Start video capture from file or camera"""
        if self.cap is not None:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {source}")
        
        return self.cap.isOpened()

    def get_frame(self):
        """Get a single frame from the video source"""
        if self.cap is None:
            return None

        ret, frame = self.cap.read()
        if ret:
            self.frames_queue.append(frame)
            return frame
        return None

    def get_frame_sequence(self):
        """Get the current sequence of frames"""
        if len(self.frames_queue) == self.sequence_length:
            return list(self.frames_queue)
        return None

    def release(self):
        """Release the video capture"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.frames_queue.clear()

    def __del__(self):
        """Cleanup on deletion"""
        self.release()