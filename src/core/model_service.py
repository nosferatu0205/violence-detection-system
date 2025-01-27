import cv2
import numpy as np
import joblib
from pathlib import Path

class ModelService:
    def __init__(self, config_manager, model_path='models/violence_detection_model.joblib', 
                 config_path='models/model_config.joblib'):
        """Initialize the model service"""
        self.config_manager = config_manager
        try:
            self.model = joblib.load(model_path)
            self.config = joblib.load(config_path)
            self.sequence_length = self.config['SEQUENCE_LENGTH']
            self.image_height = self.config['IMAGE_HEIGHT']
            self.image_width = self.config['IMAGE_WIDTH']
            self.classes = self.config['CLASSES_LIST']
            self.processing_settings = self.config_manager.get_processing_settings()
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def update_processing_settings(self, performance_mode):
        """Update processing settings based on performance mode"""
        self.processing_settings = self.config_manager.get_processing_settings(performance_mode)

    def preprocess_frame(self, frame):
        """Preprocess a single frame"""
        try:
            # Apply resize factor based on performance settings
            if self.processing_settings['resize_factor'] != 1.0:
                h, w = frame.shape[:2]
                new_size = (int(w * self.processing_settings['resize_factor']), 
                          int(h * self.processing_settings['resize_factor']))
                frame = cv2.resize(frame, new_size)
            
            # Resize to model input size
            resized = cv2.resize(frame, (self.image_height, self.image_width))
            normalized = resized / 255.0
            return normalized
        except Exception as e:
            raise RuntimeError(f"Frame preprocessing failed: {str(e)}")

    def predict_frames(self, frames):
        """Make prediction on a sequence of frames"""
        if len(frames) != self.sequence_length:
            raise ValueError(f"Expected {self.sequence_length} frames, got {len(frames)}")
        
        try:
            # Prepare frames
            processed_frames = np.array([self.preprocess_frame(frame) for frame in frames])
            # Make prediction
            prediction = self.model.predict(np.expand_dims(processed_frames, axis=0))[0]
            # Get class and confidence
            predicted_class = self.classes[np.argmax(prediction)]
            confidence = float(prediction[np.argmax(prediction)])
            
            return predicted_class, confidence
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {str(e)}")

    def get_frame_sequence_size(self):
        """Return the required number of frames for prediction"""
        return self.sequence_length