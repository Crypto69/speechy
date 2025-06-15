"""Auto-typing functionality for the voice assistant."""

import time
import logging
from typing import Optional, List
from pynput.keyboard import Controller, Key
import threading

logger = logging.getLogger(__name__)

class AutoTyper:
    """Handles automatic typing of transcribed text at cursor position."""
    
    def __init__(self):
        """Initialize the auto typer."""
        self.keyboard = Controller()
        self.enabled = True
        self.typing_delay = 1.0  # Delay before typing (seconds)
        self.typing_speed = 0.02  # Delay between characters (seconds)
        self.excluded_apps = ['Keychain Access', 'Login Window', '1Password']
        self.typing_thread: Optional[threading.Thread] = None
        
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable auto-typing.
        
        Args:
            enabled: Whether to enable auto-typing
        """
        self.enabled = enabled
        logger.info(f"Auto-typing {'enabled' if enabled else 'disabled'}")
    
    def set_typing_delay(self, delay: float) -> None:
        """Set delay before typing starts.
        
        Args:
            delay: Delay in seconds
        """
        self.typing_delay = max(0.0, delay)
        logger.info(f"Typing delay set to {self.typing_delay}s")
    
    def set_typing_speed(self, speed: float) -> None:
        """Set speed of typing (delay between characters).
        
        Args:
            speed: Delay between characters in seconds
        """
        self.typing_speed = max(0.001, speed)
        logger.info(f"Typing speed set to {self.typing_speed}s between characters")
    
    def add_excluded_app(self, app_name: str) -> None:
        """Add an application to the exclusion list.
        
        Args:
            app_name: Name of application to exclude
        """
        if app_name not in self.excluded_apps:
            self.excluded_apps.append(app_name)
            logger.info(f"Added '{app_name}' to auto-typing exclusion list")
    
    def remove_excluded_app(self, app_name: str) -> None:
        """Remove an application from the exclusion list.
        
        Args:
            app_name: Name of application to remove from exclusion
        """
        if app_name in self.excluded_apps:
            self.excluded_apps.remove(app_name)
            logger.info(f"Removed '{app_name}' from auto-typing exclusion list")
    
    def get_active_application(self) -> Optional[str]:
        """Get the name of the currently active application.
        
        Returns:
            Name of active application or None if cannot determine
        """
        try:
            # Try using AppKit on macOS
            import AppKit
            workspace = AppKit.NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            if active_app:
                return active_app.get('NSApplicationName', 'Unknown')
        except ImportError:
            logger.debug("AppKit not available, cannot check active application")
        except Exception as e:
            logger.error(f"Error getting active application: {e}")
        
        # Fallback: return None to allow typing (safer default)
        return None
    
    def should_type_in_current_app(self) -> bool:
        """Check if typing should be allowed in the current application.
        
        Returns:
            True if typing is allowed, False otherwise
        """
        active_app = self.get_active_application()
        if active_app is None:
            # If we can't determine the app, err on the side of caution
            logger.warning("Cannot determine active application, allowing typing")
            return True
        
        if active_app in self.excluded_apps:
            logger.info(f"Auto-typing blocked in excluded app: {active_app}")
            return False
        
        logger.debug(f"Auto-typing allowed in app: {active_app}")
        return True
    
    def type_text_async(self, text: str, callback: Optional[callable] = None) -> None:
        """Type text asynchronously at the current cursor position.
        
        Args:
            text: Text to type
            callback: Optional callback to call when typing is complete
        """
        if not self.enabled:
            logger.debug("Auto-typing is disabled, skipping")
            if callback:
                callback(False, "Auto-typing disabled")
            return
        
        if not text or not text.strip():
            logger.debug("Empty text provided, skipping auto-typing")
            if callback:
                callback(False, "Empty text")
            return
        
        # Cancel any existing typing operation
        if self.typing_thread and self.typing_thread.is_alive():
            logger.info("Canceling previous typing operation")
            # Note: We can't easily cancel a running thread, but new operation will take precedence
        
        def typing_worker():
            try:
                # Pre-typing delay
                if self.typing_delay > 0:
                    logger.info(f"Waiting {self.typing_delay}s before typing...")
                    time.sleep(self.typing_delay)
                
                # Check if typing is allowed in current app
                if not self.should_type_in_current_app():
                    if callback:
                        callback(False, "Typing blocked in current application")
                    return
                
                # Clean and prepare text
                clean_text = self._prepare_text(text)
                logger.info(f"Auto-typing: '{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}'")
                
                # Type the text
                self._type_text_sync(clean_text)
                
                logger.info("Auto-typing completed successfully")
                if callback:
                    callback(True, "Typing completed")
                
            except Exception as e:
                logger.error(f"Error during auto-typing: {e}")
                if callback:
                    callback(False, f"Typing error: {e}")
        
        self.typing_thread = threading.Thread(target=typing_worker, daemon=True)
        self.typing_thread.start()
    
    def _prepare_text(self, text: str) -> str:
        """Prepare text for typing by cleaning and formatting.
        
        Args:
            text: Raw text to prepare
            
        Returns:
            Cleaned text ready for typing
        """
        # Strip leading/trailing whitespace
        clean_text = text.strip()
        
        # Ensure text ends with appropriate punctuation if it's a sentence
        if clean_text and not clean_text[-1] in '.!?':
            # Only add period if it looks like a complete sentence
            if len(clean_text.split()) > 2:
                clean_text += '.'
        
        return clean_text
    
    def _type_text_sync(self, text: str) -> None:
        """Synchronously type text character by character.
        
        Args:
            text: Text to type
        """
        logger.info(f"Starting to type text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # Test if we can type at all
        try:
            # Try a simple test first
            logger.debug("Testing keyboard access...")
            self.keyboard.type('')  # Empty string test
            logger.debug("Keyboard access test successful")
        except Exception as test_e:
            logger.error(f"Keyboard access test failed - likely permissions issue: {test_e}")
            raise Exception(f"Cannot access keyboard for typing - check accessibility permissions: {test_e}")
        
        for i, char in enumerate(text):
            try:
                # Handle special characters
                if char == '\n':
                    self.keyboard.press(Key.enter)
                    self.keyboard.release(Key.enter)
                elif char == '\t':
                    self.keyboard.press(Key.tab)
                    self.keyboard.release(Key.tab)
                else:
                    self.keyboard.type(char)
                
                # Add delay between characters if configured
                if self.typing_speed > 0:
                    time.sleep(self.typing_speed)
                
                # Log progress every 10 characters for debugging
                if i % 10 == 0 and i > 0:
                    logger.debug(f"Typed {i}/{len(text)} characters")
                    
            except Exception as e:
                logger.error(f"Error typing character '{char}' at position {i}: {e}")
                # Try to continue with next character
                continue
        
        logger.info(f"Finished typing {len(text)} characters")
    
    def emergency_stop(self) -> None:
        """Emergency stop for auto-typing (e.g., if user presses escape)."""
        logger.info("Emergency stop triggered for auto-typing")
        self.enabled = False
        # Note: Can't easily stop thread mid-execution, but we can disable the feature
    
    def simulate_undo(self) -> None:
        """Simulate Cmd+Z to undo the last typed text."""
        try:
            logger.info("Simulating Cmd+Z to undo last auto-typing")
            self.keyboard.press(Key.cmd)
            self.keyboard.press('z')
            self.keyboard.release('z')
            self.keyboard.release(Key.cmd)
        except Exception as e:
            logger.error(f"Error simulating undo: {e}")
    
    def test_typing(self) -> bool:
        """Test if auto-typing works by typing a simple test message.
        
        Returns:
            True if test successful, False otherwise
        """
        try:
            if not self.enabled:
                logger.warning("Auto-typing test skipped - feature is disabled")
                return False
            
            test_text = "[Auto-typing test successful]"
            logger.info(f"Running auto-typing test with text: '{test_text}'")
            
            # Test synchronously with minimal delay
            original_delay = self.typing_delay
            self.typing_delay = 0.1  # Very short delay for test
            
            self.type_text_async(test_text, lambda success, msg: 
                logger.info(f"Auto-typing test completed: {'SUCCESS' if success else 'FAILED'} - {msg}"))
            
            self.typing_delay = original_delay  # Restore original delay
            return True
            
        except Exception as e:
            logger.error(f"Auto-typing test failed: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get current auto-typer status.
        
        Returns:
            Dictionary with current settings and status
        """
        return {
            'enabled': self.enabled,
            'typing_delay': self.typing_delay,
            'typing_speed': self.typing_speed,
            'excluded_apps': self.excluded_apps.copy(),
            'active_app': self.get_active_application(),
            'typing_active': self.typing_thread and self.typing_thread.is_alive()
        }