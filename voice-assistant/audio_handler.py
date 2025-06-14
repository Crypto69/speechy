"""Audio recording and processing functionality for the voice assistant."""

import pyaudio
import wave
import numpy as np
import threading
import queue
import time
import os
import tempfile
import logging
from typing import Optional, Callable, List

logger = logging.getLogger(__name__)

class AudioHandler:
    """Handles audio recording from microphone with real-time processing."""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024, 
                 channels: int = 1, format_type: int = pyaudio.paInt16,
                 device_index: Optional[int] = None):
        """Initialize audio handler.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Size of audio chunks
            channels: Number of audio channels (1 for mono)
            format_type: Audio format (paInt16 for 16-bit)
            device_index: Specific audio device index, None for default
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format_type = format_type
        self.device_index = device_index
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.recording = False
        self.audio_queue = queue.Queue()
        self.audio_data: List[bytes] = []
        self.recording_thread: Optional[threading.Thread] = None
        
        # Audio level monitoring
        self.audio_level = 0.0
        self.level_callback: Optional[Callable[[float], None]] = None
        
        # Validate audio device
        self._validate_device()
        
    def _validate_device(self) -> None:
        """Validate the audio device configuration."""
        try:
            if self.device_index is not None:
                device_info = self.audio.get_device_info_by_index(self.device_index)
                logger.info(f"Using audio device: {device_info['name']}")
            else:
                device_info = self.audio.get_default_input_device_info()
                logger.info(f"Using default audio device: {device_info['name']}")
        except Exception as e:
            logger.error(f"Audio device validation failed: {e}")
            raise
    
    def list_audio_devices(self) -> List[dict]:
        """List available audio input devices.
        
        Returns:
            List of device information dictionaries
        """
        devices = []
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
            except Exception as e:
                logger.warning(f"Could not get info for device {i}: {e}")
        return devices
    
    def set_audio_level_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for audio level updates.
        
        Args:
            callback: Function to call with audio level (0.0 to 1.0)
        """
        self.level_callback = callback
    
    def _calculate_audio_level(self, audio_data: bytes) -> float:
        """Calculate audio level from raw audio data.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Audio level between 0.0 and 1.0
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Check for empty or invalid audio data
            if len(audio_array) == 0:
                return 0.0
            
            # Calculate RMS (Root Mean Square) for audio level
            # Use float64 to avoid overflow issues
            audio_squared = audio_array.astype(np.float64) ** 2
            mean_squared = np.mean(audio_squared)
            
            # Avoid sqrt of negative or NaN values
            if mean_squared <= 0 or np.isnan(mean_squared):
                return 0.0
                
            rms = np.sqrt(mean_squared)
            # Normalize to 0-1 range (assuming 16-bit audio)
            level = min(rms / 32768.0, 1.0)
            return level
        except Exception as e:
            logger.error(f"Error calculating audio level: {e}")
            return 0.0
    
    def _record_audio(self) -> None:
        """Internal method to record audio in a separate thread."""
        try:
            self.stream = self.audio.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Audio recording started")
            
            while self.recording:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_data.append(data)
                    
                    # Calculate and update audio level
                    self.audio_level = self._calculate_audio_level(data)
                    if self.level_callback:
                        self.level_callback(self.audio_level)
                        
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error initializing audio stream: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
    
    def start_recording(self) -> bool:
        """Start recording audio.
        
        Returns:
            True if recording started successfully, False otherwise
        """
        if self.recording:
            logger.warning("Recording already in progress")
            return False
        
        try:
            self.recording = True
            self.audio_data = []
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.recording = False
            return False
    
    def stop_recording(self) -> Optional[str]:
        """Stop recording and save audio to temporary file.
        
        Returns:
            Path to temporary audio file, or None if recording failed
        """
        if not self.recording:
            logger.warning("No recording in progress")
            return None
        
        self.recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)
            if self.recording_thread.is_alive():
                logger.warning("Recording thread did not finish gracefully")
        
        if not self.audio_data:
            logger.warning("No audio data recorded")
            return None
        
        try:
            # Create temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.close()
            
            # Write audio data to WAV file
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format_type))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_data))
            
            logger.info(f"Audio saved to: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            return None
    
    def get_audio_level(self) -> float:
        """Get current audio level.
        
        Returns:
            Current audio level between 0.0 and 1.0
        """
        return self.audio_level
    
    def is_recording(self) -> bool:
        """Check if currently recording.
        
        Returns:
            True if recording, False otherwise
        """
        return self.recording
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary audio file.
        
        Args:
            file_path: Path to temporary file to delete
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary file {file_path}: {e}")
    
    def close(self) -> None:
        """Close audio handler and cleanup resources."""
        if self.recording:
            self.stop_recording()
        
        # Ensure recording thread is properly cleaned up
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
            
        if self.audio:
            self.audio.terminate()
            logger.info("Audio handler closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()