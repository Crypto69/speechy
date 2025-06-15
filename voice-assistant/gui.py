"""GUI and system tray interface for the voice assistant."""

import sys
import os
import logging
from typing import Optional, Callable
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QPushButton, QTextEdit, QProgressBar,
                            QSystemTrayIcon, QMenu, QAction, QMessageBox, QFrame,
                            QComboBox, QCheckBox, QSpinBox, QGroupBox, QTabWidget,
                            QSplitter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap, QPainter

logger = logging.getLogger(__name__)

class RecordingIndicator(QWidget):
    """Custom widget to show recording status with animated indicator."""
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.audio_level = 0.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.blink_state = False
        
    def set_recording(self, recording: bool):
        """Set recording state."""
        self.recording = recording
        if recording:
            self.timer.start(100)  # Update every 100ms
        else:
            self.timer.stop()
        self.update()
    
    def set_audio_level(self, level: float):
        """Set audio level (0.0 to 1.0)."""
        self.audio_level = max(0.0, min(1.0, level))
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event for recording indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        if self.recording:
            # Animate blinking for recording state
            self.blink_state = not self.blink_state
            if self.blink_state:
                painter.setBrush(QColor(255, 50, 50, 180))  # Red with transparency
            else:
                painter.setBrush(QColor(255, 50, 50, 100))  # Dimmer red
            
            # Draw recording circle
            circle_size = min(width, height) - 4
            x = (width - circle_size) // 2
            y = (height - circle_size) // 2
            painter.drawEllipse(x, y, circle_size, circle_size)
            
            # Draw audio level bar
            if self.audio_level > 0:
                bar_width = int(width * 0.8)
                bar_height = 4
                bar_x = (width - bar_width) // 2
                bar_y = height - 10
                
                # Background bar
                painter.setBrush(QColor(100, 100, 100))
                painter.drawRect(bar_x, bar_y, bar_width, bar_height)
                
                # Level bar
                level_width = int(bar_width * self.audio_level)
                if self.audio_level < 0.3:
                    color = QColor(0, 255, 0)  # Green for low
                elif self.audio_level < 0.7:
                    color = QColor(255, 255, 0)  # Yellow for medium
                else:
                    color = QColor(255, 0, 0)  # Red for high
                
                painter.setBrush(color)
                painter.drawRect(bar_x, bar_y, level_width, bar_height)
        else:
            # Draw idle state (gray circle)
            painter.setBrush(QColor(128, 128, 128, 100))
            circle_size = min(width, height) - 4
            x = (width - circle_size) // 2
            y = (height - circle_size) // 2
            painter.drawEllipse(x, y, circle_size, circle_size)

class VoiceAssistantGUI(QMainWindow):
    """Main GUI window for the voice assistant."""
    
    # Signals
    transcription_requested = pyqtSignal(str)  # Audio file path
    settings_changed = pyqtSignal(dict)  # New settings
    
    def __init__(self, config, hotkey_manager=None):
        super().__init__()
        self.config = config
        self.hotkey_manager = hotkey_manager
        
        # State variables
        self.recording = False
        self.transcribing = False
        self.generating = False
        self.model_loading = False
        
        # Callbacks
        self.toggle_recording_callback: Optional[Callable] = None
        
        self.init_ui()
        self.init_system_tray()
        self.apply_theme()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 800, 600)
        
        # Set application icon (not system tray icon)
        icon_path = os.path.join(os.path.dirname(__file__), "icon.icns")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Main tab
        self.create_main_tab()
        
        # Settings tab
        self.create_settings_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_main_tab(self):
        """Create the main application tab."""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Recording status section
        status_group = QGroupBox("Recording Status")
        status_layout = QHBoxLayout(status_group)
        
        # Recording indicator
        self.recording_indicator = RecordingIndicator()
        self.recording_indicator.setFixedSize(60, 60)
        status_layout.addWidget(self.recording_indicator)
        
        # Status labels
        status_text_layout = QVBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_text_layout.addWidget(self.status_label)
        
        self.hotkey_label = QLabel(f"Hotkey: {self.config.get_hotkey().upper()} (Press once to start/stop)")
        status_text_layout.addWidget(self.hotkey_label)
        
        status_layout.addLayout(status_text_layout)
        status_layout.addStretch()
        
        # Manual recording button
        self.record_button = QPushButton("Toggle Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        status_layout.addWidget(self.record_button)
        
        layout.addWidget(status_group)
        
        # Results section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        # Create splitter for transcription and response
        splitter = QSplitter(Qt.Vertical)
        
        # Transcription area
        transcription_widget = QWidget()
        transcription_layout = QVBoxLayout(transcription_widget)
        transcription_layout.addWidget(QLabel("Transcription:"))
        
        self.transcription_text = QTextEdit()
        self.transcription_text.setMaximumHeight(150)
        self.transcription_text.setPlaceholderText("Transcribed speech will appear here...")
        transcription_layout.addWidget(self.transcription_text)
        
        splitter.addWidget(transcription_widget)
        
        # LLM Response area
        response_widget = QWidget()
        response_layout = QVBoxLayout(response_widget)
        response_layout.addWidget(QLabel("AI Response:"))
        
        self.response_text = QTextEdit()
        self.response_text.setPlaceholderText("AI response will appear here...")
        response_layout.addWidget(self.response_text)
        
        splitter.addWidget(response_widget)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        results_layout.addWidget(splitter)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.copy_transcription_btn = QPushButton("Copy Transcription")
        self.copy_transcription_btn.clicked.connect(self.copy_transcription)
        button_layout.addWidget(self.copy_transcription_btn)
        
        self.copy_response_btn = QPushButton("Copy Response")
        self.copy_response_btn.clicked.connect(self.copy_response)
        button_layout.addWidget(self.copy_response_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        results_layout.addLayout(button_layout)
        
        layout.addWidget(results_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.tab_widget.addTab(main_widget, "Main")
        
    def create_settings_tab(self):
        """Create the settings tab."""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Audio settings
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QVBoxLayout(audio_group)
        
        # Hotkey setting
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Hotkey:"))
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.addItems(['f9', 'f10', 'f11', 'f12', 'ctrl+space', 'alt+space'])
        self.hotkey_combo.setMinimumWidth(150)
        self.hotkey_combo.setCurrentText(self.config.get_hotkey())
        hotkey_layout.addWidget(self.hotkey_combo)
        hotkey_layout.addStretch()
        audio_layout.addLayout(hotkey_layout)
        
        # Audio device selection would go here (requires pyaudio device enumeration)
        
        layout.addWidget(audio_group)
        
        # Model settings
        model_group = QGroupBox("Model Settings")
        model_layout = QVBoxLayout(model_group)
        
        # Whisper model
        whisper_layout = QHBoxLayout()
        whisper_layout.addWidget(QLabel("Whisper Model:"))
        self.whisper_combo = QComboBox()
        self.whisper_combo.addItems(['tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 'medium', 'medium.en', 'large'])
        self.whisper_combo.setMinimumWidth(200)
        self.whisper_combo.setCurrentText(self.config.get_whisper_model())
        whisper_layout.addWidget(self.whisper_combo)
        whisper_layout.addStretch()
        model_layout.addLayout(whisper_layout)
        
        # Ollama model
        ollama_layout = QHBoxLayout()
        ollama_layout.addWidget(QLabel("Ollama Model:"))
        self.ollama_combo = QComboBox()
        self.ollama_combo.setEditable(True)
        self.ollama_combo.addItems(['llama3.2:3b', 'llama3.2:1b', 'llama3.1:8b', 'llama3:latest', 'mistral', 'codellama'])
        self.ollama_combo.setMinimumWidth(200)
        self.ollama_combo.setCurrentText(self.config.get_ollama_model())
        ollama_layout.addWidget(self.ollama_combo)
        ollama_layout.addStretch()
        model_layout.addLayout(ollama_layout)
        
        layout.addWidget(model_group)
        
        # Feature settings
        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout(features_group)
        
        self.log_transcriptions_cb = QCheckBox("Log transcriptions to file")
        self.log_transcriptions_cb.setChecked(self.config.should_log_transcriptions())
        features_layout.addWidget(self.log_transcriptions_cb)
        
        self.notifications_cb = QCheckBox("Enable notifications")
        self.notifications_cb.setChecked(self.config.is_notification_enabled())
        features_layout.addWidget(self.notifications_cb)
        
        self.clipboard_cb = QCheckBox("Auto-copy to clipboard")
        self.clipboard_cb.setChecked(self.config.should_copy_to_clipboard())
        features_layout.addWidget(self.clipboard_cb)
        
        layout.addWidget(features_group)
        
        # Save settings button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_settings_btn = QPushButton("Save Settings")
        self.save_settings_btn.clicked.connect(self.save_settings)
        save_layout.addWidget(self.save_settings_btn)
        layout.addLayout(save_layout)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
    
    def init_system_tray(self):
        """Initialize system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available")
            return
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create a simple icon (colored circle)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 120, 200))
        painter.drawEllipse(1, 1, 14, 14)
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("Voice Assistant")
        
        # Create context menu
        tray_menu = QMenu()
        
        # Recording actions
        self.start_recording_action = QAction("Start Recording", self)
        self.start_recording_action.triggered.connect(self.toggle_recording)
        tray_menu.addAction(self.start_recording_action)
        
        self.stop_recording_action = QAction("Stop Recording", self)
        self.stop_recording_action.triggered.connect(self.toggle_recording)
        self.stop_recording_action.setVisible(False)  # Initially hidden
        tray_menu.addAction(self.stop_recording_action)
        
        tray_menu.addSeparator()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        tray_menu.addAction(about_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def apply_theme(self):
        """Apply the selected theme."""
        theme = self.config.get_gui_theme()
        
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555555;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QTextEdit {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 3px;
                }
                QPushButton {
                    background-color: #4a4a4a;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 5px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:pressed {
                    background-color: #3a3a3a;
                }
                QComboBox {
                    background-color: #4a4a4a;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 3px;
                }
            """)
    
    def set_callbacks(self, toggle_recording_cb: Callable):
        """Set callback function for recording control."""
        self.toggle_recording_callback = toggle_recording_cb
    
    def toggle_recording(self):
        """Toggle manual recording."""
        # Don't allow recording if models are still loading
        if self.model_loading:
            self.statusBar().showMessage("Please wait for models to finish loading...", 3000)
            return
            
        if self.toggle_recording_callback:
            self.toggle_recording_callback()
    
    def set_recording_state(self, recording: bool):
        """Update recording state in GUI."""
        self.recording = recording
        self.recording_indicator.set_recording(recording)
        
        if recording:
            self.status_label.setText("Recording...")
            self.record_button.setText("Stop Recording")
            self.statusBar().showMessage("Recording audio...")
            # Update tray menu
            if hasattr(self, 'start_recording_action'):
                self.start_recording_action.setVisible(False)
                self.stop_recording_action.setVisible(True)
        else:
            self.status_label.setText("Ready")
            self.record_button.setText("Start Recording")
            self.statusBar().showMessage("Ready")
            # Update tray menu
            if hasattr(self, 'start_recording_action'):
                self.start_recording_action.setVisible(True)
                self.stop_recording_action.setVisible(False)
    
    def set_audio_level(self, level: float):
        """Update audio level indicator."""
        self.recording_indicator.set_audio_level(level)
    
    def set_transcribing_state(self, transcribing: bool):
        """Update transcribing state in GUI."""
        self.transcribing = transcribing
        
        if transcribing:
            self.status_label.setText("Transcribing...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.statusBar().showMessage("Transcribing audio...")
        else:
            self.progress_bar.setVisible(False)
            if not self.generating and not self.model_loading:
                self.status_label.setText("Ready")
                self.statusBar().showMessage("Ready")
    
    def set_generating_state(self, generating: bool):
        """Update LLM generation state in GUI."""
        self.generating = generating
        
        if generating:
            self.status_label.setText("Generating response...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.statusBar().showMessage("Generating AI response...")
        else:
            self.progress_bar.setVisible(False)
            if not self.transcribing and not self.model_loading:
                self.status_label.setText("Ready")
                self.statusBar().showMessage("Ready")
    
    def set_model_loading_state(self, loading: bool):
        """Update model loading state in GUI."""
        self.model_loading = loading
        
        # Disable/enable recording button based on model loading state
        self.record_button.setEnabled(not loading)
        
        # Also disable tray menu recording actions
        if hasattr(self, 'start_recording_action'):
            self.start_recording_action.setEnabled(not loading)
        if hasattr(self, 'stop_recording_action'):
            self.stop_recording_action.setEnabled(not loading)
        
        if loading:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.progress_bar.setVisible(False)
            if not self.transcribing and not self.generating:
                self.status_label.setText("Ready")
                self.statusBar().showMessage("Ready")
    
    def set_transcription(self, text: str):
        """Set transcription text."""
        self.transcription_text.setPlainText(text)
    
    def set_response(self, text: str):
        """Set AI response text."""
        self.response_text.setPlainText(text)
    
    def copy_transcription(self):
        """Copy transcription to clipboard."""
        import pyperclip
        text = self.transcription_text.toPlainText()
        if text:
            pyperclip.copy(text)
            self.statusBar().showMessage("Transcription copied to clipboard", 2000)
    
    def copy_response(self):
        """Copy AI response to clipboard."""
        import pyperclip
        text = self.response_text.toPlainText()
        if text:
            pyperclip.copy(text)
            self.statusBar().showMessage("Response copied to clipboard", 2000)
    
    def clear_results(self):
        """Clear all text areas."""
        self.transcription_text.clear()
        self.response_text.clear()
        self.statusBar().showMessage("Results cleared", 2000)
    
    def save_settings(self):
        """Save settings from GUI to config."""
        # Update config with GUI values
        self.config.set("hotkey", self.hotkey_combo.currentText())
        self.config.set("whisper_model", self.whisper_combo.currentText())
        self.config.set("ollama_model", self.ollama_combo.currentText())
        self.config.set("log_transcriptions", self.log_transcriptions_cb.isChecked())
        self.config.set("notification_enabled", self.notifications_cb.isChecked())
        self.config.set("copy_to_clipboard", self.clipboard_cb.isChecked())
        
        # Update hotkey label
        self.hotkey_label.setText(f"Hotkey: {self.config.get_hotkey().upper()} (Press once to start/stop)")
        
        # Emit settings changed signal
        self.settings_changed.emit(self.config.config)
        
        self.statusBar().showMessage("Settings saved", 2000)
    
    def show_window(self):
        """Show the main window."""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def quit_application(self):
        """Quit the application."""
        self.close()
        QApplication.quit()
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h3>Voice Assistant</h3>
        <p>A voice-to-text application using OpenAI Whisper and Ollama.</p>
        
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time audio recording</li>
        <li>Local speech-to-text with Whisper</li>
        <li>AI response generation with Ollama</li>
        <li>Hotkey support (F9)</li>
        <li>System tray integration</li>
        </ul>
        
        <p><b>Usage:</b></p>
        <ul>
        <li>Press F9 or use GUI button to start/stop recording</li>
        <li>Right-click system tray for quick access</li>
        <li>Configure settings in the Settings tab</li>
        </ul>
        
        <p>Add your custom text here...</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About Voice Assistant")
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def show_notification(self, title: str, message: str):
        """Show system notification."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 3000)