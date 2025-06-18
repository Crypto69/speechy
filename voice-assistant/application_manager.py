"""Application lifecycle management for Speechy - Your AI Voice Assistant."""

import sys
import os
import logging
import socket
import multiprocessing
import platform
import subprocess
from PyQt5.QtWidgets import QApplication, QMessageBox

logger = logging.getLogger(__name__)


class ApplicationManager:
    """Manages application lifecycle, initialization, and cleanup."""
    
    def __init__(self):
        self.app = None
        self.socket = None
        self.voice_assistant = None
    
    def setup_logging(self):
        """Configure application logging."""
        logs_dir = self._get_logs_dir()
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, 'voice_assistant.log')),
                logging.StreamHandler()
            ]
        )
        logger.info("🎤 Speechy - Your AI Voice Assistant")
        logger.info("Logging configured")
    
    def _get_logs_dir(self):
        """Get the logs directory, creating it if it doesn't exist."""
        if getattr(sys, 'frozen', False):
            # Running as bundled app - use user home directory
            logs_dir = os.path.expanduser("~/.speechy/logs")
        else:
            # Running as script
            logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
    
    def create_application(self):
        """Create and configure Qt application."""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Speechy")
        self.app.setApplicationVersion("1.0")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when window is closed
        logger.info("Qt application created")
        return self.app
    
    def check_single_instance(self):
        """Ensure only one instance of the application is running."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('127.0.0.1', 8765))  # Use a specific port for this app
            self.socket.listen(1)
            logger.info("Single instance check passed")
            return True
        except socket.error:
            logger.error("Another instance of Speechy is already running")
            QMessageBox.warning(
                None, 
                "Speechy - Your AI Voice Assistant", 
                "Another instance is already running!"
            )
            return False
    
    def initialize_voice_assistant(self):
        """Initialize the voice assistant components."""
        # Use comprehensive permission manager
        from permission_manager import PermissionManager
        
        logger.info("Initializing comprehensive permission checking...")
        permission_manager = PermissionManager()
        permissions = permission_manager.check_all_permissions()
        
        # Log the results
        if permissions['accessibility']:
            logger.info("✅ Accessibility permissions ready - hotkeys and auto-typing will work")
        else:
            logger.warning("⚠️  Accessibility permissions missing - hotkeys and auto-typing will not work")
        
        if permissions['input_monitoring']:
            logger.info("✅ Input monitoring permissions ready - global hotkeys will work")
        else:
            logger.warning("⚠️  Input monitoring permissions missing - global hotkeys will not work")
        
        if permissions['microphone']:
            logger.info("✅ Microphone permissions ready - recording will work")
        else:
            logger.warning("⚠️  Microphone permissions missing - recording will not work")
        
        from voice_assistant import VoiceAssistant
        
        self.voice_assistant = VoiceAssistant()
        self.voice_assistant.init_gui(self.app)
        
        # Connect permission manager to GUI
        if self.voice_assistant.gui:
            self.voice_assistant.gui.set_permission_manager(permission_manager)
            
            # Show permissions tab first if any permissions are missing
            missing_permissions = [k for k, v in permissions.items() if not v]
            if missing_permissions:
                logger.info(f"Missing permissions detected: {missing_permissions}")
                logger.info("Showing permissions tab to guide user...")
                # Set permissions tab as active
                self.voice_assistant.gui.tab_widget.setCurrentIndex(1)  # Permissions is the second tab
            
            self.voice_assistant.gui.show()
        
        # Start assistant
        self.voice_assistant.start()
        
        logger.info("Voice assistant initialized")
    
    def setup_cleanup(self):
        """Setup application cleanup handlers."""
        def cleanup():
            try:
                if self.voice_assistant:
                    self.voice_assistant.stop()
                if self.socket:
                    self.socket.close()
                logger.info("Application cleanup completed")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        
        self.app.aboutToQuit.connect(cleanup)
    
    def run(self):
        """Run the main application loop."""
        try:
            logger.info("Starting Speechy - Your AI Voice Assistant")
            return self.app.exec_()
        except Exception as e:
            logger.error(f"Error in main application loop: {e}")
            self._show_error_dialog(f"Application error: {e}")
            return 1
    
    def _show_error_dialog(self, error_message: str):
        """Show error dialog to user."""
        try:
            if not self.app:
                self.app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Speechy - Your AI Voice Assistant Error")
            msg.setText(f"Fatal error occurred:\n\n{error_message}")
            msg.exec_()
        except Exception:
            # Fallback to console output if GUI fails
            print(f"Fatal error: {error_message}")
    
    def start_application(self):
        """Complete application startup sequence."""
        try:
            # Setup multiprocessing support for PyInstaller
            multiprocessing.freeze_support()
            
            # Initialize logging
            self.setup_logging()
            
            # Create Qt application
            self.create_application()
            
            # Check for existing instances
            if not self.check_single_instance():
                return 1
            
            # Initialize voice assistant
            self.initialize_voice_assistant()
            
            # Setup cleanup handlers
            self.setup_cleanup()
            
            # Run main loop
            return self.run()
            
        except Exception as e:
            logger.error(f"Fatal error during application startup: {e}")
            self._show_error_dialog(str(e))
            return 1


def main():
    """Main application entry point."""
    app_manager = ApplicationManager()
    return app_manager.start_application()


if __name__ == "__main__":
    sys.exit(main())