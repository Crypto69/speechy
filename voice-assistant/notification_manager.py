"""Notification management for Speechy - Your AI Voice Assistant."""

import logging
from typing import Optional
from plyer import notification

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages system notifications and messages."""
    
    def __init__(self, gui=None):
        """Initialize notification manager with optional GUI reference."""
        self.gui = gui
        self.enabled = True
    
    def set_gui(self, gui):
        """Set GUI reference for tray notifications."""
        self.gui = gui
    
    def set_enabled(self, enabled: bool):
        """Enable or disable notifications."""
        self.enabled = enabled
    
    def show_notification(self, title: str, message: str, timeout: int = 3000):
        """Show system notification using the best available method."""
        if not self.enabled:
            return
            
        try:
            # Try GUI tray notification first (better integration)
            if self.gui and hasattr(self.gui, 'show_notification'):
                self.gui.show_notification(title, message)
            else:
                # Fallback to plyer notification
                notification.notify(
                    title=title,
                    message=message,
                    timeout=timeout // 1000  # plyer uses seconds, not milliseconds
                )
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
    def show_transcription_complete(self, transcription: str):
        """Show notification for completed transcription."""
        preview = transcription[:100] + "..." if len(transcription) > 100 else transcription
        self.show_notification("Transcription Complete", preview)
    
    def show_response_ready(self):
        """Show notification for AI response completion."""
        self.show_notification("AI Response Ready", "Response generated successfully")
    
    def show_error(self, error_message: str):
        """Show error notification."""
        self.show_notification("Speechy Error", error_message)
    
    def show_recording_started(self):
        """Show notification when recording starts."""
        self.show_notification("Recording Started", "Speak now...")
    
    def show_recording_stopped(self):
        """Show notification when recording stops."""
        self.show_notification("Recording Stopped", "Processing audio...")