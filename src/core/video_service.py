from collections import deque
import numpy as np
import cv2

class VideoService:
    def __init__(self, config_manager, sequence_length):
        """Initialize video service"""
        self.config_manager = config_manager
        self.cap = None
        self.sequence_length = sequence_length
        self.frames_queue = deque(maxlen=sequence_length)
        self.frame_count = 0
        self.processing_settings = self.config_manager.get_processing_settings()
        self.current_source = None
        self.playback_speed = 1.5  # Speed multiplier
        self.original_fps = None
        
    def get_available_cameras(self):
        """Get list of available camera devices with names"""
        available_cameras = []
        try:
            # Try to get default camera first
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    name = f"Default Camera ({width}x{height})"
                else:
                    name = "Default Camera"
                available_cameras.append({"id": 0, "name": name})
                cap.release()

            # If we found the default camera, don't need to check index 0 again
            start_idx = 1 if available_cameras else 0
            
            # Check additional cameras
            for i in range(start_idx, 2):  # Only check first two indices to avoid long startup
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        ret, _ = cap.read()
                        if ret:
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            name = f"Camera {i} ({width}x{height})"
                        else:
                            name = f"Camera {i}"
                        available_cameras.append({"id": i, "name": name})
                        cap.release()
                except Exception:
                    continue
        except Exception as e:
            print(f"Error detecting cameras: {str(e)}")
            
        # If no cameras found, add a dummy entry for testing
        if not available_cameras:
            available_cameras.append({"id": 0, "name": "Default Camera"})
            
        return available_cameras

    def switch_source(self, source):
        """Switch to a different video source without stopping detection"""
        if self.current_source == source:
            return True
            
        try:
            new_cap = cv2.VideoCapture(source)
            if new_cap.isOpened():
                if self.cap is not None:
                    self.cap.release()
                self.cap = new_cap
                self.current_source = source
                self.frames_queue.clear()
                
                # Store original FPS
                self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
                if self.original_fps == 0:  # For cameras that don't report FPS
                    self.original_fps = 30.0
                    
                return True
            else:
                new_cap.release()
                return False
        except Exception:
            return False

    def start_video_capture(self, source):
        """Start video capture from file or camera"""
        return self.switch_source(source)

    def get_frame(self):
        """Get a single frame from the video source"""
        if self.cap is None:
            return None

        # Skip frames based on performance settings and playback speed
        skip_frames = self.processing_settings['frame_skip']
        speed_skip = max(0, int((self.playback_speed - 1) * self.original_fps / 10))
        total_skip = skip_frames + speed_skip
        
        frame = None
        for _ in range(total_skip + 1):
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

    def release(self):
        """Release the video capture"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.frames_queue.clear()
            self.frame_count = 0

    def update_processing_settings(self, performance_mode):
        """Update processing settings based on performance mode"""
        self.processing_settings = self.config_manager.get_processing_settings(performance_mode)
        self.frame_count = 0  # Reset frame count

    def set_playback_speed(self, speed):
        """Set the playback speed multiplier"""
        self.playback_speed = speed

    def __del__(self):
        """Cleanup on deletion"""
        self.release()