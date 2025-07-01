"""Hotkey management for Speechy - Your AI Voice Assistant."""

import logging
import threading
import time
from typing import Optional, Set
from PyQt5.QtCore import QObject, pyqtSignal
from pynput import keyboard

logger = logging.getLogger(__name__)


class HotkeyManager(QObject):
    """Manages global hotkey detection."""
    
    hotkey_toggled = pyqtSignal()  # Single signal for toggle behavior
    
    def __init__(self, hotkey_string: str):
        super().__init__()
        self.hotkey_string = hotkey_string
        self.listener: Optional[keyboard.Listener] = None
        self.hotkey_combo: Optional[Set] = None
        self.pressed_keys: Set = set()
        self.last_hotkey_state = False  # Track if hotkey combo is currently pressed
        
        # Auto-typing state management
        self.typing_in_progress = False
        self.typing_lock = threading.Lock()
        
        self.parse_hotkey()
        
    def parse_hotkey(self):
        """Parse hotkey string into key combination."""
        logger.info(f"Parsing hotkey string: '{self.hotkey_string}'")
        
        if self.hotkey_string.lower() in ['f9', 'f10', 'f11', 'f12']:
            self.hotkey_combo = {getattr(keyboard.Key, self.hotkey_string.lower())}
            logger.info(f"Set hotkey combo to F-key: {self.hotkey_combo}")
        elif self.hotkey_string.lower() == 'ctrl+space':
            self.hotkey_combo = {keyboard.Key.ctrl_l, keyboard.Key.space}
            logger.info(f"Set hotkey combo to Ctrl+Space: {self.hotkey_combo}")
        elif self.hotkey_string.lower() == 'alt+space':
            self.hotkey_combo = {keyboard.Key.alt_l, keyboard.Key.space}
            logger.info(f"Set hotkey combo to Alt+Space: {self.hotkey_combo}")
        elif self.hotkey_string.lower() in ['option+space', 'opt+space']:
            # On macOS, Option key could be alt_l, alt_r, or alt
            # We'll try multiple combinations to handle different scenarios
            self.hotkey_combo = {keyboard.Key.alt_l, keyboard.Key.space}
            logger.info(f"Set hotkey combo to Option+Space (alt_l+space): {self.hotkey_combo}")
            logger.info("Note: If this doesn't work, the Option key might be detected as alt_r or alt")
        else:
            # Default to F9
            self.hotkey_combo = {keyboard.Key.f9}
            logger.warning(f"Unknown hotkey '{self.hotkey_string}', defaulting to F9")
            
        # Log final hotkey combo for confirmation
        logger.info(f"✅ Hotkey combo configured: {self.hotkey_combo}")
        
    
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
        """Stop listening for hotkey events with proper cleanup."""
        if self.listener:
            try:
                logger.debug("Stopping hotkey listener...")
                self.listener.stop()
                
                # Wait for listener thread to properly terminate
                # This helps prevent race conditions on macOS
                if hasattr(self.listener, '_thread') and self.listener._thread:
                    self.listener._thread.join(timeout=0.1)
                    logger.debug("Listener thread joined successfully")
                
                self.listener = None
                logger.info("Hotkey listener stopped")
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}")
                self.listener = None  # Reset regardless of error
    
    def on_key_press(self, key):
        """Handle key press events."""
        logger.debug(f"Key pressed: {key}")
        
        # Skip hotkey processing if auto-typing is in progress
        with self.typing_lock:
            if self.typing_in_progress:
                logger.debug("Ignoring key press during auto-typing")
                return
        
        self.pressed_keys.add(key)
        
        # Check if hotkey combo is pressed and wasn't pressed before (toggle on press)
        if self.hotkey_combo:
            is_combo_pressed = self._is_hotkey_combo_pressed()
            
            if is_combo_pressed and not self.last_hotkey_state:
                self.last_hotkey_state = True
                logger.info(f"🎯 HOTKEY ACTIVATED: {self.hotkey_string}")
                self.hotkey_toggled.emit()
        else:
            logger.warning("No hotkey combo defined!")
    
    def _is_hotkey_combo_pressed(self):
        """Check if the hotkey combo is pressed, with flexible matching for modifier keys."""
        if not self.hotkey_combo:
            return False
            
        # For option+space, we need to handle different Option key representations
        if self.hotkey_string.lower() in ['option+space', 'opt+space']:
            # Check for space key
            space_pressed = keyboard.Key.space in self.pressed_keys
            # Check for any alt key variant (alt_l, alt_r, alt)
            alt_pressed = any(key in self.pressed_keys for key in [
                keyboard.Key.alt_l, keyboard.Key.alt_r, 
                getattr(keyboard.Key, 'alt', None)
            ] if key is not None)
            
            return space_pressed and alt_pressed
        
        # For other combos, use standard subset matching
        return self.hotkey_combo.issubset(self.pressed_keys)
    
    def on_key_release(self, key):
        """Handle key release events."""
        # Skip processing if auto-typing is in progress
        with self.typing_lock:
            if self.typing_in_progress:
                logger.debug("Ignoring key release during auto-typing")
                return
        
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        
        # Reset hotkey state when any part of the combo is released
        if self.hotkey_combo and self._is_key_part_of_combo(key):
            self.last_hotkey_state = False
    
    def _is_key_part_of_combo(self, key):
        """Check if a key is part of the current hotkey combo."""
        if not self.hotkey_combo:
            return False
            
        # For option+space, check if it's space or any alt key
        if self.hotkey_string.lower() in ['option+space', 'opt+space']:
            alt_keys = [keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt]
            return (key == keyboard.Key.space or key in alt_keys)
        
        # For other combos, use standard membership check
        return key in self.hotkey_combo
    
    def update_hotkey(self, new_hotkey: str):
        """Update the hotkey combination without restarting listener to prevent crashes."""
        try:
            logger.info(f"Updating hotkey from '{self.hotkey_string}' to '{new_hotkey}'")
            old_hotkey = self.hotkey_string
            
            # Clear current key states to prevent false triggers
            self.pressed_keys.clear()
            self.last_hotkey_state = False
            
            # Update hotkey configuration
            self.hotkey_string = new_hotkey
            self.parse_hotkey()
            
            # The listener remains active and will automatically use the new hotkey_combo
            # This avoids the segmentation fault that occurs when restarting pynput listeners
            logger.info(f"Hotkey successfully updated from '{old_hotkey}' to '{new_hotkey}' (no restart required)")
            
        except Exception as e:
            logger.error(f"Failed to update hotkey from '{self.hotkey_string}' to '{new_hotkey}': {e}")
            logger.exception("Hotkey update exception:")
            # Reset to a safe state without touching the listener
            self.pressed_keys.clear()
            self.last_hotkey_state = False
    
    def restart_listening(self):
        """Restart the hotkey listener with thread safety delay."""
        try:
            logger.info("Restarting hotkey listener...")
            self.stop_listening()
            
            # Add delay to ensure proper thread cleanup on macOS
            # This prevents race conditions that can cause segmentation faults
            time.sleep(0.15)  # 150ms delay for thread safety
            logger.debug("Thread cleanup delay completed")
            
            self.start_listening()
            logger.info("Hotkey listener restart completed successfully")
        except Exception as e:
            logger.error(f"Error during hotkey listener restart: {e}")
            logger.exception("Hotkey restart failed:")
    
    def suspend_hotkeys(self):
        """Suspend hotkey detection during auto-typing to prevent feedback loops."""
        with self.typing_lock:
            if not self.typing_in_progress:
                self.typing_in_progress = True
                # Clear any stale key states that might cause false triggers
                self.pressed_keys.clear()
                self.last_hotkey_state = False
                logger.debug("Hotkeys suspended for auto-typing")
    
    def resume_hotkeys(self):
        """Resume hotkey detection after auto-typing completes."""
        with self.typing_lock:
            if self.typing_in_progress:
                self.typing_in_progress = False
                # Clear key states to prevent stale combinations
                self.pressed_keys.clear()
                self.last_hotkey_state = False
                logger.debug("Hotkeys resumed after auto-typing")