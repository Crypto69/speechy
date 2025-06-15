"""Main application entry point for Speechy - Your AI Voice Assistant."""

import sys
import os
import logging
import tempfile
import threading
import time
from typing import Optional

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from pynput import keyboard
import pyperclip
from plyer import notification

# Import our modules
from config import Config
from audio_handler import AudioHandler
from transcriber import WhisperTranscriber
from llm_client import OllamaClient
from gui import VoiceAssistantGUI
from auto_typer import AutoTyper

# Configure logging with proper path handling for bundled app
def get_logs_dir():
    """Get the logs directory, creating it if it doesn't exist."""
    if getattr(sys, 'frozen', False):
        # Running as bundled app - use user home directory
        logs_dir = os.path.expanduser("~/.speechy/logs")
    else:
        # Running as script
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

logs_dir = get_logs_dir()
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'voice_assistant.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class HotkeyManager(QObject):
    """Manages global hotkey detection."""
    
    hotkey_toggled = pyqtSignal()  # Single signal for toggle behavior
    
    def __init__(self, hotkey_string: str):
        super().__init__()
        self.hotkey_string = hotkey_string
        self.listener: Optional[keyboard.Listener] = None
        self.hotkey_combo = None
        self.pressed_keys = set()
        self.last_hotkey_state = False  # Track if hotkey combo is currently pressed
        self.parse_hotkey()
        
    def parse_hotkey(self):
        """Parse hotkey string into key combination."""
        if self.hotkey_string.lower() in ['f9', 'f10', 'f11', 'f12']:
            self.hotkey_combo = {getattr(keyboard.Key, self.hotkey_string.lower())}
        elif self.hotkey_string.lower() == 'ctrl+space':
            self.hotkey_combo = {keyboard.Key.ctrl_l, keyboard.Key.space}
        elif self.hotkey_string.lower() == 'alt+space':
            self.hotkey_combo = {keyboard.Key.alt_l, keyboard.Key.space}
        else:
            # Default to F9
            self.hotkey_combo = {keyboard.Key.f9}
            logger.warning(f"Unknown hotkey '{self.hotkey_string}', defaulting to F9")
        
    
    def start_listening(self):
        """Start listening for hotkey events."""
        if self.listener:
            self.stop_listening()
        
        try:
            self.listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.listener.start()
            logger.info(f"Hotkey listener started for: {self.hotkey_string}")
            logger.info("If hotkeys don't work, use the 'Toggle Recording' button in the GUI")
        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")
            logger.info("Hotkey listener failed - use the GUI button to record")
    
    def stop_listening(self):
        """Stop listening for hotkey events."""
        if self.listener:
            self.listener.stop()
            self.listener = None
            logger.info("Hotkey listener stopped")
    
    def on_key_press(self, key):
        """Handle key press events."""
        self.pressed_keys.add(key)
        
        # Check if hotkey combo is pressed and wasn't pressed before (toggle on press)
        if (self.hotkey_combo and 
            self.hotkey_combo.issubset(self.pressed_keys) and 
            not self.last_hotkey_state):
            self.last_hotkey_state = True
            logger.info(f"Hotkey activated: {self.hotkey_string}")
            self.hotkey_toggled.emit()
    
    def on_key_release(self, key):
        """Handle key release events."""
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        
        # Reset hotkey state when any part of the combo is released
        if self.hotkey_combo and key in self.hotkey_combo:
            self.last_hotkey_state = False
    
    def update_hotkey(self, new_hotkey: str):
        """Update the hotkey combination."""
        self.hotkey_string = new_hotkey
        self.parse_hotkey()
        if self.listener:
            self.restart_listening()
    
    def restart_listening(self):
        """Restart the hotkey listener."""
        self.stop_listening()
        self.start_listening()

class VoiceAssistant(QObject):
    """Main voice assistant application."""
    
    # Signals for thread-safe GUI updates
    status_message_signal = pyqtSignal(str)
    transcribing_state_signal = pyqtSignal(bool)
    generating_state_signal = pyqtSignal(bool)
    model_loading_state_signal = pyqtSignal(bool)
    transcription_signal = pyqtSignal(str)
    response_signal = pyqtSignal(str)
    audio_level_signal = pyqtSignal(float)
    
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
        
        # State variables
        self.recording = False
        self.current_audio_file: Optional[str] = None
        self.recording_start_time: Optional[float] = None
        
        # Setup logging directory (already handled by get_logs_dir function)
        
        # Initialize components
        self.init_components()
        
    def init_components(self):
        """Initialize all components."""
        try:
            # Initialize audio handler
            self.audio_handler = AudioHandler(
                sample_rate=self.config.get_audio_sample_rate(),
                chunk_size=self.config.get_audio_chunk_size(),
                device_index=self.config.get_audio_device_index()
            )
            self.audio_handler.set_audio_level_callback(self.on_audio_level_update)
            logger.info("Audio handler initialized")
            
            # Initialize transcriber
            self.transcriber = WhisperTranscriber(
                model_size=self.config.get_whisper_model()
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
            
            # Connect signals for thread-safe GUI updates
            self.status_message_signal.connect(self.gui.statusBar().showMessage)
            self.transcribing_state_signal.connect(self.gui.set_transcribing_state)
            self.generating_state_signal.connect(self.gui.set_generating_state)
            self.model_loading_state_signal.connect(self.gui.set_model_loading_state)
            self.transcription_signal.connect(self.gui.set_transcription)
            self.response_signal.connect(self.gui.set_response)
            self.audio_level_signal.connect(self.gui.set_audio_level)
            
            # Ensure auto-typer settings are synchronized with current config
            if self.auto_typer:
                self.auto_typer.set_enabled(self.config.is_auto_typing_enabled())
                logger.info(f"Auto-typer enabled status set to: {self.config.is_auto_typing_enabled()}")
            
            # Set reference to voice assistant in GUI for auto-typer testing
            self.gui._voice_assistant = self
            
            # Load Whisper model in background
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
                if self.gui:
                    self.model_loading_state_signal.emit(True)
                
                # Load Whisper model
                if self.gui:
                    self.status_message_signal.emit("Loading Whisper model...")
                
                if self.transcriber and not self.transcriber.load_model():
                    logger.error("Failed to load Whisper model")
                    if self.gui:
                        self.status_message_signal.emit("Failed to load Whisper model")
                        self.model_loading_state_signal.emit(False)
                    return
                
                # Check Ollama connection
                if self.gui:
                    self.status_message_signal.emit("Checking Ollama connection...")
                
                if self.llm_client and not self.llm_client.is_server_available():
                    logger.warning("Ollama server not available")
                    if self.gui:
                        self.status_message_signal.emit("Ollama server not available")
                else:
                    logger.info("Ollama server connection verified")
                
                # Signal model loading has completed
                if self.gui:
                    self.model_loading_state_signal.emit(False)
                    self.status_message_signal.emit("Ready")
                
                logger.info("Models loaded successfully")
                
            except Exception as e:
                logger.error(f"Error loading models: {e}")
                if self.gui:
                    self.status_message_signal.emit(f"Error loading models: {e}")
                    self.model_loading_state_signal.emit(False)
        
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
                    
                    # Process the audio asynchronously
                    self.process_audio_async(self.current_audio_file)
                else:
                    logger.warning("No audio data recorded")
                    if self.gui:
                        self.gui.statusBar().showMessage("No audio recorded", 3000)
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            if self.gui:
                self.gui.statusBar().showMessage(f"Recording error: {e}", 3000)
    
    def process_audio_async(self, audio_file_path: str):
        """Process audio file asynchronously."""
        def process_worker():
            try:
                # Transcribe audio
                if self.gui:
                    self.transcribing_state_signal.emit(True)
                
                transcription = None
                if self.transcriber:
                    transcription = self.transcriber.transcribe_file(audio_file_path)
                
                if self.gui:
                    self.transcribing_state_signal.emit(False)
                
                if transcription:
                    logger.info(f"Transcription: {transcription}")
                    
                    if self.gui:
                        self.transcription_signal.emit(transcription)
                    
                    # Log transcription if enabled
                    if self.config.should_log_transcriptions():
                        self.log_transcription(transcription)
                    
                    # Copy to clipboard if enabled
                    if self.config.should_copy_to_clipboard():
                        pyperclip.copy(transcription)
                    
                    # Auto-type transcription if enabled and mode is "raw" or "both"
                    if (self.auto_typer and self.config.is_auto_typing_enabled() and 
                        self.config.get_auto_typing_mode() in ["raw", "both"]):
                        def typing_callback(success: bool, message: str):
                            if success:
                                logger.info("Auto-typing completed successfully")
                            else:
                                logger.warning(f"Auto-typing failed: {message}")
                        
                        self.auto_typer.type_text_async(transcription, typing_callback)
                    
                    # Generate LLM response
                    self.generate_llm_response_async(transcription)
                    
                    # Show notification if enabled
                    if self.config.is_notification_enabled():
                        self.show_notification("Transcription Complete", transcription[:100] + "..." if len(transcription) > 100 else transcription)
                    
                else:
                    logger.warning("Transcription failed or empty")
                    if self.gui:
                        self.status_message_signal.emit("Transcription failed")
                
                # Clean up temporary audio file
                if self.audio_handler:
                    self.audio_handler.cleanup_temp_file(audio_file_path)
                    
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                if self.gui:
                    self.status_message_signal.emit(f"Processing error: {e}")
                    self.transcribing_state_signal.emit(False)
        
        thread = threading.Thread(target=process_worker, daemon=True)
        thread.start()
    
    def generate_llm_response_async(self, prompt: str):
        """Generate LLM response asynchronously."""
        def generate_worker():
            try:
                if self.gui:
                    self.generating_state_signal.emit(True)
                
                response = None
                if self.llm_client:
                    # System prompt for transcription correction and intent clarity
                    system_prompt = """You are a transcription correction assistant. Your job is to:
1. Fix any obvious speech-to-text errors (like "cold started" instead of "called started")
2. Remove filler words (um, uh, you know, like, etc.)
3. Clean up grammar and make the text more readable
4. Understand and preserve the original intent and meaning
5. Return ONLY the corrected text, nothing else
6. Your output should be a clean, corrected version of the input text without any additional commentary or explanations.
7. Add punctuation where are use specifies it, but do not add any additional punctuation. For example:
- if the user says "Full stop" or "period" then you should add a full stop at that point.
- if the user says "comma" then you should add a comma at that point.
- if the user says "question mark" then you should add a question mark at that point.

Examples:
- "I called started the server" → "I cold started the server"
- "I would like to um, start you know the server" → "I would like to start the server"
- "Can you uh, help me with this thing" → "Can you help me with this"
- "I think we should comma like, go now full stop" → "I think we should, go now."

Fix this transcription:"""
                    
                    response = self.llm_client.generate_response(
                        prompt, 
                        system_prompt=system_prompt,
                        temperature=0.2  # Lower temperature for more consistent corrections
                    )
                
                if self.gui:
                    self.generating_state_signal.emit(False)
                
                if response:
                    logger.info(f"LLM Response: {response[:100]}...")
                    
                    if self.gui:
                        self.response_signal.emit(response)
                    
                    # Auto-type corrected response if enabled and mode is "corrected" 
                    if (self.auto_typer and self.config.is_auto_typing_enabled() and 
                        self.config.get_auto_typing_mode() == "corrected"):
                        def typing_callback(success: bool, message: str):
                            if success:
                                logger.info("Auto-typing corrected text completed successfully")
                            else:
                                logger.warning(f"Auto-typing corrected text failed: {message}")
                        
                        self.auto_typer.type_text_async(response, typing_callback)
                    
                    # Show notification if enabled
                    if self.config.is_notification_enabled():
                        self.show_notification("AI Response Ready", "Response generated successfully")
                        
                else:
                    logger.warning("LLM response failed or empty")
                    if self.gui:
                        self.status_message_signal.emit("AI response failed")
                
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")
                if self.gui:
                    self.status_message_signal.emit(f"AI response error: {e}")
                    self.generating_state_signal.emit(False)
        
        thread = threading.Thread(target=generate_worker, daemon=True)
        thread.start()
    
    def on_audio_level_update(self, level: float):
        """Handle audio level updates."""
        if self.gui and self.recording:
            self.audio_level_signal.emit(float(level))
    
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
                    model_size=new_settings.get('whisper_model', 'base')
                )
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
    
    def show_notification(self, title: str, message: str):
        """Show system notification."""
        try:
            if self.gui:
                self.gui.show_notification(title, message)
            else:
                # Fallback to plyer notification
                notification.notify(
                    title=title,
                    message=message,
                    timeout=3
                )
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
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

def main():
    """Main application entry point."""
    try:
        # Create QApplication with instance checking
        app = QApplication(sys.argv)
        
        # Check if another instance is already running
        app.setApplicationName("Speechy")
        app.setApplicationVersion("1.0")
        
        # Prevent multiple instances using Qt's built-in mechanism
        import socket
        
        # Try to create a local socket server to detect other instances
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', 8765))  # Use a specific port for this app
            sock.listen(1)
        except socket.error:
            logger.error("Another instance of Voice Assistant is already running")
            QMessageBox.warning(None, "Speechy - Your AI Voice Assistant", "Another instance is already running!")
            sys.exit(1)
        
        app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed
        
        # Create voice assistant
        assistant = VoiceAssistant()
        
        # Initialize GUI
        assistant.init_gui(app)
        
        # Show GUI
        if assistant.gui:
            assistant.gui.show()
        
        # Start assistant
        assistant.start()
        
        # Handle application shutdown
        def cleanup():
            try:
                assistant.stop()
                sock.close()  # Clean up the socket
            except:
                pass
        
        app.aboutToQuit.connect(cleanup)
        
        # Run application
        logger.info("Starting voice assistant application")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        
        # Show error dialog if possible
        try:
            app = QApplication.instance() 
            if not app:
                app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Speechy - Your AI Voice Assistant Error")
            msg.setText(f"Fatal error occurred:\n\n{str(e)}")
            msg.exec_()
            
        except:
            print(f"Fatal error: {e}")
        
        sys.exit(1)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # Required for PyInstaller on Windows/macOS
    main()