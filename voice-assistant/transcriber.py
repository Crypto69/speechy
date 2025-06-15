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
            
            # Set up model cache directory for bundled apps
            import sys
            download_root = None
            local_files_only = False
            
            if getattr(sys, 'frozen', False):
                # Running as bundled app - try multiple strategies
                app_dir = os.path.dirname(sys.executable)
                download_root = os.path.join(app_dir, 'whisper_models')
                
                # Force a more reliable model for bundled apps
                if self.model_size == "small.en":
                    logger.info("Forcing 'base' model for bundled app (small.en has issues)")
                    self.model_size = "base"
                
                # Try to create the directory, but don't fail if we can't due to read-only filesystem
                try:
                    os.makedirs(download_root, exist_ok=True)
                    logger.info(f"Using bundled app model directory: {download_root}")
                except OSError as e:
                    logger.warning(f"Cannot create model directory in app bundle: {e}")
                    # Fall back to user's home directory
                    download_root = os.path.expanduser("~/whisper_models")
                    os.makedirs(download_root, exist_ok=True)
                    logger.info(f"Using user home model directory: {download_root}")
            
            # Try loading with the configured download root first
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device=device,
                    compute_type=compute_type,
                    download_root=download_root,
                    local_files_only=local_files_only
                )
                logger.info(f"Model loaded successfully from: {download_root}")
            except Exception as model_error:
                logger.warning(f"Failed to load model with custom download_root: {model_error}")
                # Fallback: try with default cache directory
                logger.info("Trying fallback with default cache directory...")
                try:
                    self.model = WhisperModel(
                        self.model_size,
                        device=device,
                        compute_type=compute_type,
                        download_root=None,  # Use default
                        local_files_only=False
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback model loading also failed: {fallback_error}")
                    # Last resort: try with 'tiny' model which is more reliable
                    if self.model_size != "tiny":
                        logger.info("Trying with 'tiny' model as last resort...")
                        self.model_size = "tiny"  # Update the model size
                        self.model = WhisperModel(
                            "tiny",
                            device=device,
                            compute_type=compute_type,
                            download_root=None,
                            local_files_only=False
                        )
                        logger.warning("Fell back to 'tiny' Whisper model due to loading issues")
                    else:
                        raise fallback_error
            
            # Validate the model works by doing a quick test
            try:
                # Create a small test audio array (1 second of silence)
                import numpy as np
                test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence at 16kHz
                segments, info = self.model.transcribe(test_audio, beam_size=1)
                list(segments)  # Force evaluation
                logger.info("Model validation successful")
            except Exception as validation_error:
                logger.error(f"Model validation failed: {validation_error}")
                # If model fails validation, try to reload it
                self.model = None
                raise Exception(f"Model failed validation: {validation_error}")
            
            self.model_loaded = True
            logger.info(f"Whisper model {self.model_size} loaded and validated successfully")
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
            
            # Check audio file size and properties
            file_size = os.path.getsize(audio_file_path)
            logger.info(f"Audio file size: {file_size} bytes")
            
            if file_size < 1000:  # Less than 1KB is probably too short
                logger.warning(f"Audio file appears to be very small ({file_size} bytes), may be empty or too short")
            
            # Try to get more info about the audio file
            try:
                import wave
                import numpy as np
                with wave.open(audio_file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    sample_rate = wf.getframerate()
                    duration = frames / sample_rate
                    channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    
                    logger.info(f"Audio file: {duration:.2f}s duration, {sample_rate} Hz, {frames} frames, {channels} channels, {sample_width} bytes per sample")
                    
                    if duration < 0.5:
                        logger.warning(f"Audio recording is very short ({duration:.2f}s), may not contain speech")
                    
                    # Read and analyze audio data
                    audio_data = wf.readframes(frames)
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    
                    # Calculate audio statistics
                    max_amplitude = np.max(np.abs(audio_array))
                    rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
                    logger.info(f"Audio analysis: max_amplitude={max_amplitude}, rms={rms:.1f}, max_possible={32767}")
                    
                    if max_amplitude < 1000:
                        logger.warning(f"Audio amplitude is very low ({max_amplitude}), recording may be too quiet")
                    
                    # Check for silence
                    silence_threshold = 100
                    non_silent_samples = np.sum(np.abs(audio_array) > silence_threshold)
                    silence_ratio = 1 - (non_silent_samples / len(audio_array))
                    logger.info(f"Silence analysis: {silence_ratio:.1%} of audio is below threshold")
                    
                    if silence_ratio > 0.8:
                        logger.warning("Audio appears to be mostly silent")
                        
            except Exception as wave_e:
                logger.warning(f"Could not read audio file properties: {wave_e}")
            
            start_time = time.time()
            
            # Use even more lenient settings for problematic audio in bundled apps
            # Transcribe the audio
            segments, info = self.model.transcribe(
                audio_file_path,
                language=language,
                beam_size=1,  # Reduce beam size for speed and consistency
                temperature=0.3,  # Add some temperature to avoid repetitive outputs
                compression_ratio_threshold=1.8,  # More lenient
                log_prob_threshold=-1.5,  # More lenient 
                no_speech_threshold=0.2,  # Much more lenient
                condition_on_previous_text=False,
                initial_prompt="This is a clear recording of someone speaking.",
                word_timestamps=False,
                prepend_punctuations="\"'([{-",
                append_punctuations="\"'.,:!?)]}"
            )
            
            logger.info(f"Whisper detected language: {info.language} (confidence: {info.language_probability:.2f})")
            
            # Combine all segments into a single text
            transcribed_text = ""
            segment_count = 0
            for segment in segments:
                logger.debug(f"Segment {segment_count}: '{segment.text}' (confidence: {segment.avg_logprob:.2f})")
                transcribed_text += segment.text
                segment_count += 1
            
            logger.info(f"Total segments processed: {segment_count}")
            
            # Clean up the transcribed text
            transcribed_text = transcribed_text.strip()
            logger.info(f"Raw transcribed text: '{transcribed_text}'")
            
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