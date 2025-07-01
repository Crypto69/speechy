"""Startup management for macOS LaunchAgent integration."""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class StartupManager:
    """Manages macOS LaunchAgent for application startup at login."""
    
    def __init__(self):
        """Initialize startup manager with LaunchAgent configuration."""
        self.launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        self.plist_filename = "com.chrisventer.speechy.plist"
        self.plist_path = self.launch_agents_dir / self.plist_filename
        
        # Ensure LaunchAgents directory exists
        self.launch_agents_dir.mkdir(parents=True, exist_ok=True)
        
    def get_executable_path(self) -> str:
        """Get the path to the executable for LaunchAgent configuration.
        
        Returns:
            Path to either the bundled app or Python script
        """
        if getattr(sys, 'frozen', False):
            # Running as bundled app
            if sys.platform == 'darwin':
                # macOS app bundle - get the actual executable inside
                app_path = sys.executable
                if app_path.endswith('/MacOS/Speechy'):
                    # Return the app bundle path for open command
                    return str(Path(app_path).parent.parent.parent)
                return app_path
            return sys.executable
        else:
            # Running in development mode - need to launch with Python
            # main.py is in the same directory as this file
            current_dir = Path(__file__).parent
            main_script = current_dir / "main.py"
            if main_script.exists():
                return str(main_script.resolve())
            
            # Fallback: look for main.py in parent directory
            fallback_main = current_dir.parent / "main.py"
            if fallback_main.exists():
                return str(fallback_main.resolve())
            
            # Final fallback: return expected path
            return str(main_script.resolve())
    
    def get_python_executable(self) -> Optional[str]:
        """Get the Python executable path for development mode.
        
        Returns:
            Path to Python executable or None if in bundled mode
        """
        if not getattr(sys, 'frozen', False):
            return sys.executable
        return None
    
    def create_launchagent_plist(self) -> Dict[str, Any]:
        """Create LaunchAgent plist configuration.
        
        Returns:
            Dictionary containing plist configuration
        """
        executable_path = self.get_executable_path()
        python_executable = self.get_python_executable()
        
        # Base plist configuration
        plist_config = {
            "Label": "com.chrisventer.speechy",
            "RunAtLoad": True,
            "KeepAlive": False,
            "StandardOutPath": str(Path.home() / ".speechy" / "logs" / "startup.log"),
            "StandardErrorPath": str(Path.home() / ".speechy" / "logs" / "startup_error.log"),
        }
        
        if getattr(sys, 'frozen', False):
            # Bundled app - use open command to launch app bundle
            if executable_path.endswith('.app'):
                plist_config["ProgramArguments"] = [
                    "/usr/bin/open",
                    "-a", executable_path
                ]
            else:
                plist_config["ProgramArguments"] = [executable_path]
        else:
            # Development mode - launch with Python
            if python_executable and os.path.exists(executable_path):
                plist_config["ProgramArguments"] = [
                    python_executable,
                    executable_path
                ]
                
                # Set working directory to the project root
                project_root = str(Path(executable_path).parent)
                plist_config["WorkingDirectory"] = project_root
                
                # Preserve conda environment if active
                if 'CONDA_PREFIX' in os.environ:
                    plist_config["EnvironmentVariables"] = {
                        "PATH": os.environ.get("PATH", ""),
                        "CONDA_PREFIX": os.environ.get("CONDA_PREFIX", ""),
                        "CONDA_DEFAULT_ENV": os.environ.get("CONDA_DEFAULT_ENV", ""),
                    }
            else:
                raise ValueError(f"Cannot find Python executable or main script: {python_executable}, {executable_path}")
        
        return plist_config
    
    def write_plist_file(self, plist_config: Dict[str, Any]) -> bool:
        """Write plist configuration to file.
        
        Args:
            plist_config: Plist configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to plist XML format using plutil
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(plist_config, f, indent=2)
                temp_json = f.name
            
            # Convert JSON to plist using plutil
            result = subprocess.run([
                'plutil', '-convert', 'xml1', 
                '-o', str(self.plist_path),
                temp_json
            ], capture_output=True, text=True)
            
            # Clean up temp file
            os.unlink(temp_json)
            
            if result.returncode == 0:
                logger.info(f"LaunchAgent plist created: {self.plist_path}")
                return True
            else:
                logger.error(f"Failed to create plist: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error writing plist file: {e}")
            return False
    
    def enable_startup(self) -> bool:
        """Enable application startup at login.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create plist configuration
            plist_config = self.create_launchagent_plist()
            
            # Write plist file
            if not self.write_plist_file(plist_config):
                return False
            
            # Load the LaunchAgent
            result = subprocess.run([
                'launchctl', 'load', str(self.plist_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("LaunchAgent loaded successfully")
                return True
            else:
                # Check if already loaded (not an error)
                if "already loaded" in result.stderr.lower():
                    logger.info("LaunchAgent already loaded")
                    return True
                logger.error(f"Failed to load LaunchAgent: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling startup: {e}")
            return False
    
    def disable_startup(self) -> bool:
        """Disable application startup at login.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Unload the LaunchAgent if it exists
            if self.plist_path.exists():
                result = subprocess.run([
                    'launchctl', 'unload', str(self.plist_path)
                ], capture_output=True, text=True)
                
                # Remove plist file
                self.plist_path.unlink()
                logger.info("LaunchAgent unloaded and plist removed")
                return True
            else:
                logger.info("No LaunchAgent plist to remove")
                return True
                
        except Exception as e:
            logger.error(f"Error disabling startup: {e}")
            return False
    
    def is_startup_enabled(self) -> bool:
        """Check if startup is currently enabled.
        
        Returns:
            True if LaunchAgent is configured and loaded
        """
        try:
            # Check if plist file exists
            if not self.plist_path.exists():
                return False
            
            # Check if LaunchAgent is loaded
            result = subprocess.run([
                'launchctl', 'list', 'com.chrisventer.speechy'
            ], capture_output=True, text=True)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error checking startup status: {e}")
            return False
    
    def get_startup_info(self) -> Dict[str, Any]:
        """Get detailed startup configuration information.
        
        Returns:
            Dictionary with startup status and configuration details
        """
        info = {
            "enabled": self.is_startup_enabled(),
            "plist_exists": self.plist_path.exists(),
            "plist_path": str(self.plist_path),
            "executable_path": self.get_executable_path(),
            "is_bundled": getattr(sys, 'frozen', False),
            "launch_agents_dir": str(self.launch_agents_dir)
        }
        
        if info["plist_exists"]:
            try:
                # Read current plist configuration
                result = subprocess.run([
                    'plutil', '-convert', 'json', '-o', '-', str(self.plist_path)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    info["current_config"] = json.loads(result.stdout)
            except Exception as e:
                logger.error(f"Error reading plist configuration: {e}")
        
        return info