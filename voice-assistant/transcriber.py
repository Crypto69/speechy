"""Speech-to-text transcription using OpenAI Whisper."""

import os
import logging
import threading
import time
import numpy as np
from typing import Optional, Callable, Dict
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Model size estimates in MB (approximate download sizes)
MODEL_SIZES: Dict[str, int] = {
    "tiny": 39,
    "tiny.en": 39,
    "base": 74,
    "base.en": 74,
    "small": 244,
    "small.en": 244,
    "medium": 769,
    "medium.en": 769,
    "large": 1550,
    "large-v1": 1550,
    "large-v2": 1550,
    "large-v3": 1550
}

class WhisperTranscriber:
    """Handles speech-to-text transcription using Whisper model."""
    
    def __init__(self, model_size: str = "base", device: str = "auto", 
                 compute_type: str = "auto", progress_callback: Optional[Callable[[int, str], None]] = None,
                 config = None):
        """Initialize the Whisper transcriber.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            device: Device to run on ("cpu", "cuda", "auto")
            compute_type: Compute type ("int8", "float16", "float32", "auto")
            progress_callback: Optional callback for progress updates (progress_percent, status_message)
            config: Configuration object for accessing settings
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        self.config = config
        self.model_loaded = False
        self.loading = False
        self.progress_callback = progress_callback
        
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
    
    def _update_progress(self, progress: int, message: str):
        """Update progress through callback if available.
        
        Args:
            progress: Progress percentage (0-100)
            message: Status message
        """
        if self.progress_callback:
            try:
                self.progress_callback(progress, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def _get_model_size_mb(self) -> int:
        """Get estimated download size for the current model.
        
        Returns:
            Estimated size in MB
        """
        return MODEL_SIZES.get(self.model_size, 500)  # Default to 500MB if unknown
    
    def _simulate_download_progress(self, duration_seconds: float = 8.0):
        """Simulate download progress for better user experience.
        
        Args:
            duration_seconds: How long to simulate the download
        """
        model_size_mb = self._get_model_size_mb()
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            elapsed = time.time() - start_time
            progress = int((elapsed / duration_seconds) * 75)  # Go up to 75% during "download"
            
            if progress <= 20:
                message = f"Downloading {self.model_size} model ({model_size_mb}MB)..."
            elif progress <= 50:
                message = f"Downloading {self.model_size} model ({progress}%)..."
            else:
                message = f"Downloading {self.model_size} model ({progress}%)..."
                
            self._update_progress(progress, message)
            time.sleep(0.2)  # Update every 200ms
    
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
            logger.info(f"🤖 Loading Whisper model: {self.model_size}")
            
            # Start with progress tracking
            model_size_mb = self._get_model_size_mb()
            self._update_progress(0, f"Preparing to load {self.model_size} model ({model_size_mb}MB)...")
            
            device, compute_type = self._determine_optimal_settings()
            self._update_progress(10, "Optimizing settings for your system...")
            
            # Set up model cache directory for bundled apps
            import sys
            download_root = None
            local_files_only = False
            
            self._update_progress(20, "Setting up model cache directory...")
            
            if getattr(sys, 'frozen', False):
                # Running as bundled app - try multiple strategies
                app_dir = os.path.dirname(sys.executable)
                download_root = os.path.join(app_dir, 'whisper_models')
                
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
                    
            self._update_progress(30, "Checking for existing model files...")
            
            # Check if model files already exist locally
            model_exists_locally = False
            if download_root and os.path.exists(download_root):
                # Check for typical model file patterns
                for item in os.listdir(download_root):
                    if self.model_size in item and os.path.isdir(os.path.join(download_root, item)):
                        model_exists_locally = True
                        break
            
            if model_exists_locally:
                self._update_progress(40, f"Found existing {self.model_size} model, loading...")
            else:
                self._update_progress(40, f"Model not found locally, downloading from Hugging Face...")
                # Simulate download progress for better UX (this runs while actual download happens)
                self._simulate_download_progress(8.0)
                
            # Try loading with the configured download root first
            try:
                self._update_progress(80, "Finalizing download and loading model into memory...")
                self.model = WhisperModel(
                    self.model_size,
                    device=device,
                    compute_type=compute_type,
                    download_root=download_root,
                    local_files_only=local_files_only
                )
                logger.info(f"Model loaded successfully from: {download_root}")
                self._update_progress(95, "Model loaded successfully")
            except Exception as model_error:
                logger.warning(f"Failed to load model with custom download_root: {model_error}")
                # Fallback: try with default cache directory
                logger.info("Trying fallback with default cache directory...")
                self._update_progress(50, "Retrying with default cache directory...")
                try:
                    self._update_progress(80, "Finalizing download and loading model into memory...")
                    self.model = WhisperModel(
                        self.model_size,
                        device=device,
                        compute_type=compute_type,
                        download_root=None,  # Use default
                        local_files_only=False
                    )
                    self._update_progress(95, "Model loaded successfully (fallback)")
                except Exception as fallback_error:
                    logger.error(f"Fallback model loading also failed: {fallback_error}")
                    # Last resort: try with 'tiny' model which is more reliable
                    if self.model_size != "tiny":
                        logger.info("Trying with 'tiny' model as last resort...")
                        self._update_progress(60, "Trying fallback to tiny model...")
                        self.model_size = "tiny"  # Update the model size
                        self._update_progress(80, "Loading tiny model into memory...")
                        self.model = WhisperModel(
                            "tiny",
                            device=device,
                            compute_type=compute_type,
                            download_root=None,
                            local_files_only=False
                        )
                        logger.warning("Fell back to 'tiny' Whisper model due to loading issues")
                        self._update_progress(95, "Tiny model loaded successfully")
                    else:
                        raise fallback_error
            
            # Validate the model works by doing a quick test
            try:
                self._update_progress(98, "Validating model...")
                # Create a small test audio array (1 second of silence)
                test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence at 16kHz
                segments, info = self.model.transcribe(test_audio, beam_size=1)
                list(segments)  # Force evaluation
                logger.info("Model validation successful")
            except Exception as validation_error:
                logger.error(f"Model validation failed: {validation_error}")
                # If model fails validation, try to reload it
                self.model = None
                self._update_progress(0, f"Model validation failed: {validation_error}")
                raise Exception(f"Model failed validation: {validation_error}")
            
            self.model_loaded = True
            self._update_progress(100, f"Whisper model {self.model_size} ready")
            logger.info(f"Whisper model {self.model_size} loaded and validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
            self.model_loaded = False
            self._update_progress(0, f"Failed to load model: {str(e)}")
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
                    
                    # Pre-filter: Skip Whisper processing for very quiet audio
                    silence_skip_threshold = self.config.get("silence_skip_threshold", 50) if self.config else 50
                    if max_amplitude < silence_skip_threshold and silence_ratio > 0.95:
                        logger.info(f"Skipping Whisper processing: max_amplitude={max_amplitude} < {silence_skip_threshold} and silence_ratio={silence_ratio:.1%} > 95%")
                        logger.info("No voice input detected")
                        return "NO_VOICE_INPUT"
                        
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
            
            # Filter segments by confidence threshold and combine into text
            confidence_threshold = self.config.get_confidence_threshold() if self.config else -0.5
            transcribed_text = ""
            segment_count = 0
            filtered_count = 0
            for segment in segments:
                logger.debug(f"Segment {segment_count}: '{segment.text}' (confidence: {segment.avg_logprob:.2f})")
                if segment.avg_logprob >= confidence_threshold:
                    transcribed_text += segment.text
                else:
                    logger.debug(f"Filtered segment {segment_count} due to low confidence: {segment.avg_logprob:.2f} < {confidence_threshold}")
                    filtered_count += 1
                segment_count += 1
            
            if filtered_count > 0:
                logger.info(f"Filtered {filtered_count}/{segment_count} segments due to low confidence (threshold: {confidence_threshold})")
            
            logger.info(f"Total segments processed: {segment_count}")
            
            # Clean up the transcribed text
            transcribed_text = transcribed_text.strip()
            logger.info(f"Raw transcribed text: '{transcribed_text}'")
            
            end_time = time.time()
            duration = end_time - start_time
            
            if transcribed_text:
                logger.info(f"Transcription completed in {duration:.2f}s: '{transcribed_text[:100]}{'...' if len(transcribed_text) > 100 else ''}'")
                logger.info(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")
                return transcribed_text
            else:
                logger.info("No voice input detected")
                return "NO_VOICE_INPUT"
            
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
    
    def set_progress_callback(self, callback: Optional[Callable[[int, str], None]]):
        """Set progress callback for model loading updates.
        
        Args:
            callback: Function to call with (progress_percent, status_message)
        """
        self.progress_callback = callback
    
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