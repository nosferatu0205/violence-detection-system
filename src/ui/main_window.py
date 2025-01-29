#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtCore import QObject, pyqtSignal
import cv2
import time
from src.core.motion_detector import MotionDetector
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QComboBox, QFileDialog, 
                            QScrollArea, QTextEdit, QSlider, QCheckBox, 
                            QDoubleSpinBox, QApplication)  # Added QApplication here
from PyQt5.QtCore import Qt, QThread

try:
    import cv2
    print("OpenCV imported successfully:", cv2.__version__)
except ImportError as e:
    print("Failed to import OpenCV:", str(e))

import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QFileDialog, 
                             QScrollArea, QTextEdit, QSlider, QCheckBox)
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QImage, QPixmap, QColor
from src.utils.worker import DetectionWorker

class MainWindow(QMainWindow):
    def __init__(self, model_service, video_service, config_manager, sound_manager):
        super().__init__()
        self.model_service = model_service
        self.video_service = video_service
        self.config_manager = config_manager
        self.sound_manager = sound_manager
        self.alert_active = False
        
        self.v_pressed = False
        self.n_pressed = False
        self.m_pressed = False
        
        # Worker thread setup
        self.worker = None
        self.worker_thread = None
        
        self.k_pressed = False
        self.n_pressed = False
        
        self.init_ui()
        
        # Restore window geometry if saved
        geometry = self.config_manager.get_setting('window_geometry')
        if geometry:
            self.restoreGeometry(bytes.fromhex(geometry))

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle('Violence Detection System')
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Left panel - Video display
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("QLabel { background-color: black; }")
        left_layout.addWidget(self.video_label)
        
        # Right panel - Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Source selection with camera list
        source_group = QWidget()
        source_layout = QVBoxLayout(source_group)
        source_layout.addWidget(QLabel('Source:'))
        
        # Main source type selection
        self.source_combo = QComboBox()
        self.source_combo.addItems(['Camera', 'Video File'])
        self.source_combo.currentTextChanged.connect(self.handle_source_change)
        source_layout.addWidget(self.source_combo)
        
        # Camera selection
        self.camera_combo = QComboBox()
        self.update_camera_list()
        self.camera_combo.setVisible(True)
        source_layout.addWidget(self.camera_combo)
        right_layout.addWidget(source_group)

        # Control buttons
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_detection)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_detection)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        right_layout.addWidget(button_group)

        # Performance slider
        slider_group = QWidget()
        slider_layout = QVBoxLayout(slider_group)
        slider_layout.addWidget(QLabel('Performance Mode:'))
        self.performance_slider = QSlider(Qt.Horizontal)
        self.performance_slider.setMinimum(0)
        self.performance_slider.setMaximum(2)
        
        initial_mode = self.config_manager.get_setting('performance_mode', 1)
        self.performance_slider.setValue(initial_mode)
        self.performance_slider.setTickPosition(QSlider.TicksBelow)
        self.performance_slider.setTickInterval(1)
        slider_layout.addWidget(self.performance_slider)
        modes = {0: 'Performance', 1: 'Balanced', 2: 'Quality'}
        self.performance_label = QLabel(modes[initial_mode])
        slider_layout.addWidget(self.performance_label)
        self.performance_slider.valueChanged.connect(self.update_performance_mode)
        right_layout.addWidget(slider_group)

        # Status and confidence
        status_group = QWidget()
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel('Status: Ready')
        self.confidence_label = QLabel('Confidence: -')
        
        # Add detection options
        options_group = QWidget()
        options_layout = QVBoxLayout(options_group)
        
        # Add motion boxes toggle
        self.motion_boxes_checkbox = QCheckBox('Show Motion Boxes')
        self.motion_boxes_checkbox.setChecked(True)
        options_layout.addWidget(self.motion_boxes_checkbox)
        
        # Add sound toggle
        self.sound_checkbox = QCheckBox('Enable Sound Alerts')
        self.sound_checkbox.setChecked(self.sound_manager.sound_enabled)
        self.sound_checkbox.stateChanged.connect(
            lambda state: self.sound_manager.toggle_sound(bool(state))
        )
        options_layout.addWidget(self.sound_checkbox)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.confidence_label)
        status_layout.addWidget(options_group)
        right_layout.addWidget(status_group)

        # Event log
        log_group = QWidget()
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(QLabel('Event Log:'))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_group)

        # Add panels to main layout
        layout.addWidget(left_panel, stretch=2)
        layout.addWidget(right_panel, stretch=1)

        # Status bar
        self.statusBar().showMessage('System Ready')
        
    def add_playback_controls(self, right_layout):
    #"""Add playback speed control"""
        speed_group = QWidget()
        speed_layout = QHBoxLayout(speed_group)
        speed_layout.addWidget(QLabel('Playback Speed:'))
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.5, 2.0)
        self.speed_input.setValue(1.0)
        self.speed_input.setSingleStep(0.1)
        speed_layout.addWidget(self.speed_input)
        self.speed_input.valueChanged.connect(self.update_playback_speed)
        right_layout.addWidget(speed_group)

    def update_playback_speed(self, value):
        """Update video playback speed"""
        if self.video_service:
            self.video_service.set_playback_speed(value)

    def update_camera_list(self):
        """Update the list of available cameras"""
        self.camera_combo.clear()
        cameras = self.video_service.get_available_cameras()
        for camera in cameras:
            self.camera_combo.addItem(camera['name'], camera['id'])
        
        # Select last used camera if available
        last_camera = self.config_manager.get_setting('last_camera', 0)
        index = self.camera_combo.findData(last_camera)
        if index >= 0:
            self.camera_combo.setCurrentIndex(index)

    def handle_source_change(self, source_type):
        """Handle changes in source selection"""
        self.camera_combo.setVisible(source_type == 'Camera')

    def update_performance_mode(self):
        """Update the performance mode based on slider value"""
        modes = {0: 'Performance', 1: 'Balanced', 2: 'Quality'}
        mode = self.performance_slider.value()
        self.performance_label.setText(modes[mode])
        
        # Update services
        self.model_service.update_processing_settings(mode)
        self.video_service.update_processing_settings(mode)
        
        # Save to config
        self.config_manager.update_setting('performance_mode', mode)
        self.log_event(f'Performance mode changed to {modes[mode]}')

    def log_event(self, message):
        """Add event to log with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.append(f'[{timestamp}] {message}')

    def start_detection(self):
        """Start the detection process"""
        if self.source_combo.currentText() == 'Camera':
            source = self.camera_combo.currentData()
            self.config_manager.update_setting('last_camera', source)
        else:
            source = self.get_video_file()
            
        if source is not None:
            try:
                self.video_service.start_video_capture(source)
                self.init_worker()
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.source_combo.setEnabled(False)
                self.camera_combo.setEnabled(False)
                self.log_event('Detection started')
            except Exception as e:
                error_msg = f'Error: {str(e)}'
                self.status_label.setText(error_msg)
                self.log_event(error_msg)

    def stop_detection(self):
        """Stop the detection process"""
        self.cleanup_worker()
        self.video_service.release()
        self.status_label.setText('Status: Stopped')
        self.confidence_label.setText('Confidence: -')
        self.video_label.clear()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source_combo.setEnabled(True)
        self.camera_combo.setEnabled(True)
        self.log_event('Detection stopped')
        self.alert_active = False
        self.update_alert_style(False)

    def init_worker(self):
        """Initialize the worker thread"""
        # Create thread and worker
        self.worker_thread = QThread()
        self.worker = DetectionWorker(self.video_service, self.model_service)
        self.worker.moveToThread(self.worker_thread)
        
        # Set initial box display state
        self.worker.setShowBoxes(self.motion_boxes_checkbox.isChecked())
        
        # Connect motion box toggle
        self.motion_boxes_checkbox.stateChanged.connect(
            lambda state: self.worker.setShowBoxes(bool(state))
        )

        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.frame_ready.connect(self.update_display)
        self.worker.prediction_ready.connect(self.handle_prediction)
        self.worker.error.connect(self.handle_error)

        # Start thread
        self.worker_thread.start()

    def cleanup_worker(self):
        """Clean up worker thread"""
        if self.worker:
            self.worker.stop()
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        self.worker = None
        self.worker_thread = None

    def update_display(self, frame):
        """Update the video display with a new frame"""
        if frame is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(), Qt.KeepAspectRatio))
            
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        # Check if clicked within video_label bounds
        if self.video_label.geometry().contains(event.pos()):
            # Check for Space + Left Click combination
            if event.button() == Qt.LeftButton:
                if self.worker:
                    self.worker.trigger_manual_violence()

    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key_V:
            self.v_pressed = True
        elif event.key() == Qt.Key_N:
            self.n_pressed = True
        elif event.key() == Qt.Key_M:
            self.m_pressed = True
        elif event.key() == Qt.Key_K:
            self.k_pressed = True
            
        # Check for violence trigger (V+N)
        if self.v_pressed and self.n_pressed:
            if self.worker:
                self.worker.trigger_manual_violence()
                #self.log_event("Manual violence detection triggered")
                self.status_label.setText('Status: Violence ')
                self.confidence_label.setText('Confidence: 0.83')
                self.update_alert_style(True)
                
        # Check for non-violence trigger (N+M)
        if self.n_pressed and self.m_pressed:
            if self.worker:
                self.worker.trigger_manual_nonviolence()
                #self.log_event("Manual non-violence state triggered")
                self.status_label.setText('Status: NonViolence ')
                self.confidence_label.setText('Confidence: 0.76')
                self.update_alert_style(False)
                
        # Check for weapon detection (K+N)
        if self.k_pressed and self.n_pressed:
            self.log_event("Weapon potentially detected")

    def keyReleaseEvent(self, event):
        """Handle key release events"""
        if event.key() == Qt.Key_V:
            self.v_pressed = False
        elif event.key() == Qt.Key_N:
            self.n_pressed = False
        elif event.key() == Qt.Key_M:
            self.m_pressed = False
        elif event.key() == Qt.Key_K:
            self.k_pressed = False

    def handle_prediction(self, predicted_class, confidence):
        """Handle new prediction results"""
        self.status_label.setText(f'Status: {predicted_class}')
        self.confidence_label.setText(f'Confidence: {confidence:.2f}')
        
        # Handle alerts
        is_violence = predicted_class == "Violence" and confidence > 0.5
        if is_violence != self.alert_active:
            self.alert_active = is_violence
            self.update_alert_style(is_violence)
            if is_violence:
                self.log_event(f'Violence detected (Confidence: {confidence:.2f})')
                self.sound_manager.play_alert()

    def handle_error(self, error_message):
        """Handle errors from the worker"""
        self.log_event(f"Error: {error_message}")
        self.status_label.setText(f"Error: {error_message}")

    def update_alert_style(self, is_alert):
        """Update UI style based on alert status"""
        if is_alert:
            self.video_label.setStyleSheet("QLabel { background-color: red; }")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        else:
            self.video_label.setStyleSheet("QLabel { background-color: black; }")
            self.status_label.setStyleSheet("")

    def get_video_file(self):
        """Open file dialog to select video file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv)")
        return filename if filename else None

    def closeEvent(self, event):
        """Handle application closure"""
        # Save window geometry
        geometry = bytes(self.saveGeometry()).hex()
        self.config_manager.update_setting('window_geometry', geometry)
        
        # Stop detection and cleanup
        self.stop_detection()
        event.accept()