"""Hotkey management for Speechy - Your AI Voice Assistant."""

import logging
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