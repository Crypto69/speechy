"""Audio processing pipeline for Speechy - Your AI Voice Assistant."""

import logging
import threading
import time
from typing import Optional, Callable
import pyperclip
from PyQt5.QtCore import QObject, pyqtSignal

from prompts import PromptManager

logger = logging.getLogger(__name__)


class AudioProcessor(QObject):
    """Handles the complete audio processing pipeline."""
    
    # Signals for thread-safe GUI updates
    transcribing_state_signal = pyqtSignal(bool)
    generating_state_signal = pyqtSignal(bool)
    transcription_signal = pyqtSignal(str)
    response_signal = pyqtSignal(str)
    status_message_signal = pyqtSignal(str)
    
    def __init__(self, config, transcriber=None, llm_client=None, auto_typer=None, notification_manager=None):
        """Initialize audio processor with required components."""
        super().__init__()
        self.config = config
        self.transcriber = transcriber
        self.llm_client = llm_client
        self.auto_typer = auto_typer
        self.notification_manager = notification_manager
        self.prompt_manager = PromptManager()
        
        # Callbacks
        self.log_transcription_callback: Optional[Callable] = None
    
    def set_components(self, transcriber=None, llm_client=None, auto_typer=None, notification_manager=None):
        """Update component references."""
        if transcriber:
            self.transcriber = transcriber
        if llm_client:
            self.llm_client = llm_client
        if auto_typer:
            self.auto_typer = auto_typer
        if notification_manager:
            self.notification_manager = notification_manager
    
    def set_log_transcription_callback(self, callback: Callable):
        """Set callback for logging transcriptions."""
        self.log_transcription_callback = callback
    
    def process_audio_async(self, audio_file_path: str):
        """Process audio file asynchronously through the complete pipeline."""
        def process_worker():
            try:
                # Step 1: Transcribe audio
                transcription = self._transcribe_audio(audio_file_path)
                
                if transcription:
                    # Step 2: Handle transcription results
                    self._handle_transcription(transcription)
                    
                    # Step 3: Generate LLM response
                    self._generate_llm_response_async(transcription)
                else:
                    logger.warning("Transcription failed or empty")
                    self.status_message_signal.emit("Transcription failed")
                
                # Step 4: Clean up temporary audio file
                self._cleanup_audio_file(audio_file_path)
                    
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                self.status_message_signal.emit(f"Processing error: {e}")
                self.transcribing_state_signal.emit(False)
        
        thread = threading.Thread(target=process_worker, daemon=True)
        thread.start()
    
    def _transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe audio file to text."""
        try:
            self.transcribing_state_signal.emit(True)
            
            transcription = None
            if self.transcriber:
                transcription = self.transcriber.transcribe_file(audio_file_path)
            
            self.transcribing_state_signal.emit(False)
            
            if transcription:
                logger.info(f"Transcription: {transcription}")
                return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            self.transcribing_state_signal.emit(False)
        
        return None
    
    def _handle_transcription(self, transcription: str):
        """Handle successful transcription results."""
        # Emit transcription to GUI
        self.transcription_signal.emit(transcription)
        
        # Log transcription if enabled
        if self.config.should_log_transcriptions() and self.log_transcription_callback:
            self.log_transcription_callback(transcription)
        
        # Copy to clipboard if enabled
        if self.config.should_copy_to_clipboard():
            pyperclip.copy(transcription)
        
        # Auto-type transcription if enabled and mode is "raw" or "both"
        if (self.auto_typer and self.config.is_auto_typing_enabled() and 
            self.config.get_auto_typing_mode() in ["raw", "both"]):
            self._auto_type_text(transcription, "raw transcription")
        
        # Show notification if enabled
        if self.notification_manager and self.config.is_notification_enabled():
            self.notification_manager.show_transcription_complete(transcription)
    
    def _generate_llm_response_async(self, prompt: str):
        """Generate LLM response asynchronously."""
        def generate_worker():
            try:
                self.generating_state_signal.emit(True)
                
                response = None
                if self.llm_client:
                    system_prompt = self.prompt_manager.get_system_prompt("transcription_correction")
                    
                    response = self.llm_client.generate_response(
                        prompt, 
                        system_prompt=system_prompt,
                        temperature=0.2  # Lower temperature for more consistent corrections
                    )
                
                self.generating_state_signal.emit(False)
                
                if response:
                    self._handle_llm_response(response)
                else:
                    logger.warning("LLM response failed or empty")
                    self.status_message_signal.emit("AI response failed")
                
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")
                self.status_message_signal.emit(f"AI response error: {e}")
                self.generating_state_signal.emit(False)
        
        thread = threading.Thread(target=generate_worker, daemon=True)
        thread.start()
    
    def _handle_llm_response(self, response: str):
        """Handle successful LLM response."""
        logger.info(f"LLM Response: {response[:100]}...")
        
        # Emit response to GUI
        self.response_signal.emit(response)
        
        # Auto-type corrected response if enabled and mode is "corrected" or "both"
        if (self.auto_typer and self.config.is_auto_typing_enabled() and 
            self.config.get_auto_typing_mode() in ["corrected", "both"]):
            self._auto_type_text(response, "corrected text")
        
        # Show notification if enabled
        if self.notification_manager and self.config.is_notification_enabled():
            self.notification_manager.show_response_ready()
    
    def _auto_type_text(self, text: str, description: str):
        """Auto-type text with error handling."""
        def typing_callback(success: bool, message: str):
            if success:
                logger.info(f"Auto-typing {description} completed successfully")
            else:
                logger.warning(f"Auto-typing {description} failed: {message}")
        
        self.auto_typer.type_text_async(text, typing_callback)
    
    def _cleanup_audio_file(self, audio_file_path: str):
        """Clean up temporary audio file."""
        try:
            import os
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up audio file {audio_file_path}: {e}")
    
    def update_prompt_strategy(self, strategy: str):
        """Update the AI prompt strategy."""
        try:
            self.prompt_manager.set_strategy(strategy)
            logger.info(f"Updated prompt strategy to: {strategy}")
        except ValueError as e:
            logger.error(f"Failed to update prompt strategy: {e}")
    
    def get_available_prompt_strategies(self) -> list:
        """Get available prompt strategies."""
        return self.prompt_manager.get_available_strategies()