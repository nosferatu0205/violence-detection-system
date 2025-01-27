from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QFileDialog, 
                             QScrollArea, QTextEdit, QSlider, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import QImage, QPixmap, QColor
from src.utils.worker import DetectionWorker
import cv2
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self, model_service, video_service, config_manager, sound_manager):
        super().__init__()
        self.model_service = model_service
        self.video_service = video_service
        self.config_manager = config_manager
        self.sound_manager = sound_manager
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.alert_active = False
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
        
        # Right panel - Controls and information
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Source selection
        source_group = QWidget()
        source_layout = QVBoxLayout(source_group)
        self.source_combo = QComboBox()
        self.source_combo.addItems(['Camera', 'Video File'])
        source_layout.addWidget(QLabel('Source:'))
        source_layout.addWidget(self.source_combo)
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
        
        # Add sound toggle
        self.sound_checkbox = QCheckBox('Enable Sound Alerts')
        self.sound_checkbox.setChecked(self.sound_manager.sound_enabled)
        self.sound_checkbox.stateChanged.connect(
            lambda state: self.sound_manager.toggle_sound(bool(state))
        )
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.confidence_label)
        status_layout.addWidget(self.sound_checkbox)
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
        source = 0 if self.source_combo.currentText() == 'Camera' else self.get_video_file()
        if source is not None:
            try:
                self.video_service.start_video_capture(source)
                self.timer.start(30)  # Update every 30ms
                self.status_label.setText('Status: Running')
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.log_event('Detection started')
                self.source_combo.setEnabled(False)
            except Exception as e:
                error_msg = f'Error: {str(e)}'
                self.status_label.setText(error_msg)
                self.log_event(error_msg)

    def stop_detection(self):
        """Stop the detection process"""
        self.timer.stop()
        self.video_service.release()
        self.status_label.setText('Status: Stopped')
        self.confidence_label.setText('Confidence: -')
        self.video_label.clear()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source_combo.setEnabled(True)
        self.log_event('Detection stopped')
        self.alert_active = False
        self.update_alert_style(False)

    def get_video_file(self):
        """Open file dialog to select video file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mkv)")
        return filename if filename else None

    def update_alert_style(self, is_alert):
        """Update UI style based on alert status"""
        if is_alert:
            self.video_label.setStyleSheet("QLabel { background-color: red; }")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        else:
            self.video_label.setStyleSheet("QLabel { background-color: black; }")
            self.status_label.setStyleSheet("")

    def update_frame(self):
        """Update the video frame and run detection"""
        frame = self.video_service.get_frame()
        if frame is not None:
            # Convert frame to QImage for display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(), Qt.KeepAspectRatio))

            # Run detection if we have enough frames
            frames = self.video_service.get_frame_sequence()
            if frames is not None:
                try:
                    predicted_class, confidence = self.model_service.predict_frames(frames)
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
                        
                except Exception as e:
                    error_msg = f'Detection error: {str(e)}'
                    self.status_label.setText(error_msg)
                    self.log_event(error_msg)

    def closeEvent(self, event):
        """Handle application closure"""
        # Save window geometry
        geometry = bytes(self.saveGeometry()).hex()
        self.config_manager.update_setting('window_geometry', geometry)
        
        # Stop detection and cleanup
        self.stop_detection()
        event.accept()