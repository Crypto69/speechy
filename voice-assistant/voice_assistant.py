"""Core voice assistant coordinator for Speechy - Your AI Voice Assistant."""

import sys
import os
import logging
import time
import threading
from typing import Optional

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal

# Import our modules
from config import Config
from audio_handler import AudioHandler
from transcriber import WhisperTranscriber
from llm_client import OllamaClient
from gui import VoiceAssistantGUI
from auto_typer import AutoTyper
from hotkey_manager import HotkeyManager
from audio_processor import AudioProcessor
from notification_manager import NotificationManager

logger = logging.getLogger(__name__)


class VoiceAssistant(QObject):
    """Main voice assistant application coordinator."""
    
    # Signals for thread-safe GUI updates
    audio_level_signal = pyqtSignal(float)
    model_loading_signal = pyqtSignal(bool)
    model_loading_progress_signal = pyqtSignal(int, str)  # progress_percent, message
    status_message_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize components
        self.audio_handler: Optional[AudioHandler] = None
        self.transcriber: Optional[WhisperTranscriber] = None
        self.llm_client: Optional[OllamaClient] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.gui: Optional[VoiceAssistantGUI] = None
        self.auto_typer: Optional[AutoTyper] = None
        self.audio_processor: Optional[AudioProcessor] = None
        self.notification_manager: Optional[NotificationManager] = None
        
        # State variables
        self.recording = False
        self.current_audio_file: Optional[str] = None
        self.recording_start_time: Optional[float] = None
        
        # Initialize components
        self.init_components()
        
    def init_components(self):
        """Initialize all components."""
        try:
            logger.info("🔧 Starting component initialization")
            # Initialize notification manager first
            self.notification_manager = NotificationManager()
            logger.info("NotificationManager initialized")
            
            # Initialize audio handler
            self.audio_handler = AudioHandler(
                sample_rate=self.config.get_audio_sample_rate(),
                chunk_size=self.config.get_audio_chunk_size(),
                device_index=self.config.get_audio_device_index()
            )
            self.audio_handler.set_audio_level_callback(self.on_audio_level_update)
            logger.info("Audio handler initialized")
            
            # Initialize transcriber with progress callback
            self.transcriber = WhisperTranscriber(
                model_size=self.config.get_whisper_model(),
                progress_callback=self.on_model_loading_progress,
                config=self.config
            )
            logger.info("Transcriber initialized")
            
            # Initialize LLM client
            self.llm_client = OllamaClient(
                base_url=self.config.get_ollama_url(),
                model=self.config.get_ollama_model()
            )
            logger.info("LLM client initialized")
            
            # Initialize hotkey manager
            self.hotkey_manager = HotkeyManager(self.config.get_hotkey())
            self.hotkey_manager.hotkey_toggled.connect(self.toggle_recording)
            
            # Initialize auto-typer
            self.auto_typer = AutoTyper()
            self.auto_typer.set_enabled(self.config.is_auto_typing_enabled())
            self.auto_typer.set_typing_delay(self.config.get_auto_typing_delay())
            self.auto_typer.set_typing_speed(self.config.get_auto_typing_speed())
            for app in self.config.get_auto_typing_excluded_apps():
                self.auto_typer.add_excluded_app(app)
            logger.info("Auto-typer initialized")
            
            # Initialize audio processor
            self.audio_processor = AudioProcessor(
                config=self.config,
                transcriber=self.transcriber,
                llm_client=self.llm_client,
                auto_typer=self.auto_typer,
                notification_manager=self.notification_manager
            )
            self.audio_processor.set_log_transcription_callback(self.log_transcription)
            logger.info("Audio processor initialized")
            
            logger.info("Voice assistant components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def init_gui(self, app: QApplication):
        """Initialize the GUI."""
        try:
            self.gui = VoiceAssistantGUI(self.config, self.hotkey_manager)
            self.gui.set_callbacks(self.toggle_recording)
            self.gui.settings_changed.connect(self.on_settings_changed)
            
            # Update notification manager with GUI reference
            self.notification_manager.set_gui(self.gui)
            
            # Connect audio processor signals to GUI
            self.audio_processor.transcribing_state_signal.connect(self.gui.set_transcribing_state)
            self.audio_processor.generating_state_signal.connect(self.gui.set_generating_state)
            self.audio_processor.transcription_signal.connect(self.gui.set_transcription)
            self.audio_processor.response_signal.connect(self.gui.set_response)
            self.audio_processor.status_message_signal.connect(self.gui.statusBar().showMessage)
            
            # Connect audio level signal
            self.audio_level_signal.connect(self.gui.set_audio_level)
            
            # Connect model loading signals
            self.model_loading_signal.connect(self.gui.set_model_loading_state)
            self.model_loading_progress_signal.connect(self.gui.set_model_loading_progress)
            self.status_message_signal.connect(self.gui.statusBar().showMessage)
            
            # Ensure auto-typer settings are synchronized with current config
            if self.auto_typer:
                self.auto_typer.set_enabled(self.config.is_auto_typing_enabled())
                logger.info(f"Auto-typer enabled status set to: {self.config.is_auto_typing_enabled()}")
            
            # Set reference to voice assistant in GUI for auto-typer testing
            self.gui._voice_assistant = self
            
            # Load models in background
            self.load_models_async()
            
            logger.info("GUI initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize GUI: {e}")
            raise
    
    def load_models_async(self):
        """Load models asynchronously."""
        def load_worker():
            try:
                # Signal model loading has started
                self.model_loading_signal.emit(True)
                
                # Load Whisper model
                self.status_message_signal.emit("Loading Whisper model...")
                
                if self.transcriber and not self.transcriber.load_model():
                    logger.error("Failed to load Whisper model")
                    self.status_message_signal.emit("Failed to load Whisper model")
                    self.model_loading_signal.emit(False)
                    return
                
                # Check Ollama connection
                self.status_message_signal.emit("Checking Ollama connection...")
                
                if self.llm_client and not self.llm_client.is_server_available():
                    logger.warning("Ollama server not available")
                    self.status_message_signal.emit("Ollama server not available")
                else:
                    logger.info("Ollama server connection verified")
                
                # Signal model loading has completed
                self.model_loading_signal.emit(False)
                self.status_message_signal.emit("Ready")
                
                logger.info("Models loaded successfully")
                
            except Exception as e:
                logger.error(f"Error loading models: {e}")
                self.status_message_signal.emit(f"Error loading models: {e}")
                self.model_loading_signal.emit(False)
        
        thread = threading.Thread(target=load_worker, daemon=True)
        thread.start()
    
    def toggle_recording(self):
        """Toggle recording state (for accessibility - single key press)."""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start audio recording."""
        if self.recording:
            return
        
        try:
            if self.audio_handler and self.audio_handler.start_recording():
                self.recording = True
                self.recording_start_time = time.time()  # Track recording start time
                if self.gui:
                    # Clear transcription boxes when recording starts
                    self.gui.set_transcription("")
                    self.gui.set_response("")
                    self.gui.set_recording_state(True)
                logger.info("Recording started")
            else:
                logger.error("Failed to start recording")
                if self.gui:
                    self.gui.statusBar().showMessage("Failed to start recording", 3000)
                
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            if self.gui:
                self.gui.statusBar().showMessage(f"Recording error: {e}", 3000)
    
    def stop_recording(self):
        """Stop audio recording and process the audio."""
        if not self.recording:
            return
        
        try:
            self.recording = False
            recording_duration = 0.0
            if self.recording_start_time:
                recording_duration = time.time() - self.recording_start_time
                logger.info(f"Recording duration: {recording_duration:.2f} seconds")
            
            if self.gui:
                self.gui.set_recording_state(False)
            
            # Check minimum recording duration
            if recording_duration < 0.5:  # Less than half a second
                logger.warning(f"Recording too short ({recording_duration:.2f}s), may not contain meaningful speech")
                if self.gui:
                    self.gui.statusBar().showMessage("Recording too short - please speak for at least 1 second", 4000)
                return
            
            if self.audio_handler:
                self.current_audio_file = self.audio_handler.stop_recording()
                
                if self.current_audio_file:
                    logger.info(f"Recording stopped, saved to: {self.current_audio_file}")
                    
                    # Process the audio using the audio processor
                    if self.audio_processor:
                        self.audio_processor.process_audio_async(self.current_audio_file)
                else:
                    logger.warning("No audio data recorded")
                    if self.gui:
                        self.gui.statusBar().showMessage("No audio recorded", 3000)
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            if self.gui:
                self.gui.statusBar().showMessage(f"Recording error: {e}", 3000)
    
    def on_audio_level_update(self, level: float):
        """Handle audio level updates."""
        if self.gui and self.recording:
            self.audio_level_signal.emit(float(level))
    
    def on_model_loading_progress(self, progress: int, message: str):
        """Handle model loading progress updates.
        
        Args:
            progress: Progress percentage (0-100)
            message: Status message
        """
        # Emit signal for thread-safe GUI update
        self.model_loading_progress_signal.emit(progress, message)
    
    def on_settings_changed(self, new_settings: dict):
        """Handle settings changes from GUI."""
        try:
            # Update hotkey if changed
            new_hotkey = new_settings.get('hotkey')
            if new_hotkey != self.config.get_hotkey() and self.hotkey_manager:
                self.hotkey_manager.update_hotkey(new_hotkey)
            
            # Update other components if needed
            if new_settings.get('whisper_model') != self.config.get_whisper_model():
                # Reload transcriber with new model
                self.transcriber = WhisperTranscriber(
                    model_size=new_settings.get('whisper_model', 'base'),
                    progress_callback=self.on_model_loading_progress
                )
                self.audio_processor.set_components(transcriber=self.transcriber)
                self.load_models_async()
            
            if new_settings.get('ollama_model') != self.config.get_ollama_model():
                # Update LLM client model
                if self.llm_client:
                    self.llm_client.set_model(new_settings.get('ollama_model'))
            
            # Update auto-typer settings if they changed
            if self.auto_typer:
                if new_settings.get('auto_typing_enabled') != self.config.is_auto_typing_enabled():
                    self.auto_typer.set_enabled(new_settings.get('auto_typing_enabled', False))
                
                if new_settings.get('auto_typing_delay') != self.config.get_auto_typing_delay():
                    self.auto_typer.set_typing_delay(new_settings.get('auto_typing_delay', 1.0))
                
                if new_settings.get('auto_typing_speed') != self.config.get_auto_typing_speed():
                    self.auto_typer.set_typing_speed(new_settings.get('auto_typing_speed', 0.02))
            
            # Update notification settings
            if self.notification_manager:
                self.notification_manager.set_enabled(new_settings.get('notification_enabled', True))
            
            logger.info("Settings updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
    
    def log_transcription(self, transcription: str):
        """Log transcription to file."""
        try:
            log_file = self.config.get_log_file()
            
            # Handle bundled app read-only filesystem
            if getattr(sys, 'frozen', False):
                # Use user home directory for logs in bundled app
                log_dir = os.path.expanduser("~/.speechy/logs")
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, "transcriptions.log")
            else:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {transcription}\n")
                
        except Exception as e:
            logger.error(f"Error logging transcription: {e}")
    
    def start(self):
        """Start the voice assistant."""
        try:
            # Start hotkey listener
            if self.hotkey_manager:
                self.hotkey_manager.start_listening()
            
            logger.info("Voice assistant started successfully")
            
        except Exception as e:
            logger.error(f"Error starting voice assistant: {e}")
            raise
    
    def stop(self):
        """Stop the voice assistant."""
        try:
            # Stop recording if active
            if self.recording:
                self.stop_recording()
            
            # Stop hotkey listener
            if self.hotkey_manager:
                self.hotkey_manager.stop_listening()
            
            # Close audio handler
            if self.audio_handler:
                self.audio_handler.close()
            
            # Clean up any temporary files
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                try:
                    os.remove(self.current_audio_file)
                except:
                    pass
            
            logger.info("Voice assistant stopped")
            
        except Exception as e:
            logger.error(f"Error stopping voice assistant: {e}")