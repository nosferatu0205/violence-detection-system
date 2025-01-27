import cv2
from collections import deque
import numpy as np

class VideoService:
    def __init__(self, config_manager, sequence_length):
        """Initialize video service"""
        self.config_manager = config_manager
        self.cap = None
        self.sequence_length = sequence_length
        self.frames_queue = deque(maxlen=sequence_length)
        self.frame_count = 0
        self.processing_settings = self.config_manager.get_processing_settings()

    def update_processing_settings(self, performance_mode):
        """Update processing settings based on performance mode"""
        self.processing_settings = self.config_manager.get_processing_settings(performance_mode)
        self.frame_count = 0  # Reset frame count

    def start_video_capture(self, source):
        """Start video capture from file or camera"""
        if self.cap is not None:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {source}")
        
        # Store last used source if it's a camera
        if isinstance(source, int):
            self.config_manager.update_setting('camera_index', source)
        
        return self.cap.isOpened()

    def get_frame(self):
        """Get a single frame from the video source"""
        if self.cap is None:
            return None

        # Skip frames based on performance settings
        skip_frames = self.processing_settings['frame_skip']
        
        frame = None
        for _ in range(skip_frames + 1):
            ret, frame = self.cap.read()
            if not ret:
                return None
            self.frame_count += 1

        if frame is not None:
            self.frames_queue.append(frame)
        return frame

    def get_frame_sequence(self):
        """Get the current sequence of frames"""
        if len(self.frames_queue) == self.sequence_length:
            return list(self.frames_queue)
        return None

    def get_available_cameras(self):
        """Get list of available camera devices"""
        available_cameras = []
        for i in range(5):  # Check first 5 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        return available_cameras

    def release(self):
        """Release the video capture"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.frames_queue.clear()
            self.frame_count = 0

    def __del__(self):
        """Cleanup on deletion"""
        self.release()