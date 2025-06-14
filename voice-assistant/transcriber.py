"""Speech-to-text transcription using OpenAI Whisper."""

import os
import logging
import threading
import time
from typing import Optional, Callable
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    """Handles speech-to-text transcription using Whisper model."""
    
    def __init__(self, model_size: str = "base", device: str = "auto", 
                 compute_type: str = "auto"):
        """Initialize the Whisper transcriber.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Device to run on ("cpu", "cuda", "auto")
            compute_type: Compute type ("int8", "float16", "float32", "auto")
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        self.model_loaded = False
        self.loading = False
        
        # Threading for non-blocking operations
        self.transcription_thread: Optional[threading.Thread] = None
        
    def _determine_optimal_settings(self) -> tuple:
        """Determine optimal device and compute type based on system capabilities.
        
        Returns:
            Tuple of (device, compute_type)
        """
        import platform
        
        device = self.device
        compute_type = self.compute_type
        
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    logger.info("CUDA available, using GPU")
                else:
                    device = "cpu"
                    logger.info("CUDA not available, using CPU")
            except ImportError:
                device = "cpu"
                logger.info("PyTorch not available, using CPU")
        
        if compute_type == "auto":
            if device == "cuda":
                compute_type = "float16"  # More efficient on GPU
            else:
                # Use int8 for CPU to improve performance
                compute_type = "int8"
                
        logger.info(f"Using device: {device}, compute_type: {compute_type}")
        return device, compute_type
    
    def load_model(self) -> bool:
        """Load the Whisper model.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if self.model_loaded:
            return True
            
        if self.loading:
            logger.info("Model is already loading...")
            return False
        
        try:
            self.loading = True
            logger.info(f"Loading Whisper model: {self.model_size}")
            
            device, compute_type = self._determine_optimal_settings()
            
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                download_root=None,  # Use default cache directory
                local_files_only=False
            )
            
            self.model_loaded = True
            logger.info(f"Whisper model {self.model_size} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
            self.model_loaded = False
            return False
        finally:
            self.loading = False
    
    def transcribe_file(self, audio_file_path: str, language: Optional[str] = None) -> Optional[str]:
        """Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code (e.g., "en", "es", "fr")
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if not self.model_loaded:
            if not self.load_model():
                return None
        
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None
        
        try:
            logger.info(f"Transcribing audio file: {audio_file_path}")
            start_time = time.time()
            
            # Transcribe the audio
            segments, info = self.model.transcribe(
                audio_file_path,
                language=language,
                beam_size=5,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=False,
                initial_prompt=None,
                word_timestamps=False,
                prepend_punctuations="\"'([{-",
                append_punctuations="\"'.,:!?)]}"
            )
            
            # Combine all segments into a single text
            transcribed_text = ""
            for segment in segments:
                transcribed_text += segment.text
            
            # Clean up the transcribed text
            transcribed_text = transcribed_text.strip()
            
            end_time = time.time()
            duration = end_time - start_time
            
            if transcribed_text:
                logger.info(f"Transcription completed in {duration:.2f}s: '{transcribed_text[:100]}{'...' if len(transcribed_text) > 100 else ''}'")
                logger.info(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")
            else:
                logger.warning("No speech detected in audio")
                
            return transcribed_text if transcribed_text else None
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
    
    def transcribe_async(self, audio_file_path: str, callback: Callable[[Optional[str]], None],
                        language: Optional[str] = None) -> None:
        """Transcribe audio file asynchronously.
        
        Args:
            audio_file_path: Path to audio file
            callback: Function to call with transcription result
            language: Optional language code
        """
        def transcribe_worker():
            result = self.transcribe_file(audio_file_path, language)
            callback(result)
        
        self.transcription_thread = threading.Thread(target=transcribe_worker)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self.model_loaded
    
    def is_loading(self) -> bool:
        """Check if model is currently loading.
        
        Returns:
            True if model is loading, False otherwise
        """
        return self.loading
    
    def get_model_info(self) -> dict:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "loaded": self.model_loaded,
            "loading": self.loading
        }
    
    def get_available_models(self) -> list:
        """Get list of available Whisper model sizes.
        
        Returns:
            List of available model sizes
        """
        return ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"]
    
    def unload_model(self) -> None:
        """Unload the current model to free memory."""
        if self.model:
            del self.model
            self.model = None
            self.model_loaded = False
            logger.info("Whisper model unloaded")
    
    def __del__(self):
        """Destructor to clean up resources."""
        self.unload_model()