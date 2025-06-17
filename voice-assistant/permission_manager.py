"""macOS Permission Manager for Speechy - comprehensive permission checking and requesting."""

import logging
import platform
import subprocess
import sys
import threading
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PermissionManager:
    """Manages all macOS permissions for Speechy."""
    
    def __init__(self):
        self.is_macos = platform.system() == "Darwin"
        self.permissions = {
            'microphone': False,
            'accessibility': False,
            'input_monitoring': False
        }
        if self.is_macos:
            self._log_environment()
    
    def _log_environment(self):
        """Log environment information for debugging."""
        try:
            from Foundation import NSBundle
            
            logger.info("=" * 60)
            logger.info("ENVIRONMENT INFORMATION")
            logger.info("=" * 60)
            logger.info(f"Python: {sys.version}")
            logger.info(f"Platform: {platform.platform()}")
            logger.info(f"macOS Version: {platform.mac_ver()[0]}")
            
            # Check if running as app bundle
            try:
                bundle = NSBundle.mainBundle()
                bundle_id = bundle.bundleIdentifier()
                bundle_path = bundle.bundlePath()
                exec_path = bundle.executablePath()
                
                logger.info(f"Bundle ID: {bundle_id}")
                logger.info(f"Bundle Path: {bundle_path}")
                logger.info(f"Executable Path: {exec_path}")
                logger.info(f"Is App Bundle: {'Speechy.app' in str(bundle_path) if bundle_path else False}")
                
                # Check Info.plist values
                info_dict = bundle.infoDictionary()
                if info_dict:
                    logger.info("Info.plist Usage Descriptions:")
                    for key in ['NSMicrophoneUsageDescription', 
                               'NSAppleEventsUsageDescription',
                               'NSInputMonitoringUsageDescription']:
                        value = info_dict.get(key, "NOT FOUND")
                        if value != "NOT FOUND" and len(str(value)) > 50:
                            value = str(value)[:50] + "..."
                        logger.info(f"  {key}: {value}")
                else:
                    logger.warning("No Info.plist dictionary found in bundle")
                    
            except Exception as e:
                logger.warning(f"Bundle information check failed: {e}")
                
            logger.info("=" * 60)
            
        except ImportError as e:
            logger.warning(f"Foundation framework not available for environment logging: {e}")
        except Exception as e:
            logger.error(f"Environment logging failed: {e}")
        
    def check_all_permissions(self) -> Dict[str, bool]:
        """Check all required permissions and return status."""
        if not self.is_macos:
            logger.info("Not running on macOS - skipping permission checks")
            return {'microphone': True, 'accessibility': True, 'input_monitoring': True}
            
        logger.info("=" * 60)
        logger.info("=== STARTING COMPREHENSIVE PERMISSION CHECK ===")
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        
        # Check if running as built app or script
        import sys
        if getattr(sys, 'frozen', False):
            logger.info("🏗️  Running as BUILT APPLICATION (.app bundle)")
            logger.info(f"Executable path: {sys.executable}")
        else:
            logger.info("🐍 Running as PYTHON SCRIPT")
            logger.info(f"Python path: {sys.executable}")
        
        logger.info("=" * 60)
        
        # Check each permission type
        self.permissions['accessibility'] = self._check_accessibility_permission()
        logger.info("-" * 40)
        
        self.permissions['input_monitoring'] = self._check_input_monitoring_permission()
        logger.info("-" * 40)
        
        self.permissions['microphone'] = self._check_microphone_permission()
        logger.info("-" * 40)
        
        # Log summary
        logger.info("=" * 60)
        logger.info("=== PERMISSION CHECK SUMMARY ===")
        for perm_type, status in self.permissions.items():
            emoji = "✅" if status else "❌"
            logger.info(f"{emoji} {perm_type.upper()}: {'GRANTED' if status else 'DENIED'}")
        
        missing_perms = [k for k, v in self.permissions.items() if not v]
        if missing_perms:
            logger.warning(f"⚠️  MISSING PERMISSIONS: {missing_perms}")
        else:
            logger.info("🎉 ALL PERMISSIONS GRANTED!")
        
        logger.info("=" * 60)
        
        return self.permissions.copy()
    
    def _check_accessibility_permission(self) -> bool:
        """Check accessibility permission status."""
        logger.info("--- Checking Accessibility Permission ---")
        
        try:
            # Method 1: Use ApplicationServices (most reliable)
            try:
                import ApplicationServices
                
                # Try to call AXIsProcessTrusted properly
                trusted = ApplicationServices.AXIsProcessTrusted()
                logger.info(f"ApplicationServices.AXIsProcessTrusted(): {trusted}")
                
                if trusted:
                    logger.info("✅ Accessibility permission GRANTED via ApplicationServices")
                    return True
                else:
                    logger.warning("❌ Accessibility permission DENIED via ApplicationServices")
                    self._show_accessibility_permission_dialog()
                    return False
                    
            except (ImportError, AttributeError, TypeError) as e:
                logger.warning(f"ApplicationServices accessibility check failed: {e}, falling back to AppleScript")
                
                # Method 2: AppleScript fallback
                script = '''
                tell application "System Events"
                    try
                        set frontmostApp to name of first application process whose frontmost is true
                        return "true"
                    on error errMsg
                        return "false:" & errMsg
                    end try
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, check=False)
                
                logger.info(f"AppleScript result: {result.stdout.strip()}")
                logger.info(f"AppleScript stderr: {result.stderr.strip()}")
                
                if result.stdout.strip().startswith("true"):
                    logger.info("✅ Accessibility permission GRANTED via AppleScript")
                    return True
                else:
                    logger.warning("❌ Accessibility permission DENIED via AppleScript")
                    self._show_accessibility_permission_dialog()
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking accessibility permission: {e}")
            return False
    
    def _check_input_monitoring_permission(self) -> bool:
        """Check input monitoring permission status."""
        logger.info("--- Checking Input Monitoring Permission ---")
        
        try:
            # Use Quartz directly to check input monitoring without creating problematic listeners
            try:
                import Quartz
                # Try to get current modifier flags - this should work if we have input monitoring permission
                event_flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateCombinedSessionState)
                logger.info(f"Successfully got event flags: {event_flags}")
                logger.info("✅ Input Monitoring permission GRANTED")
                return True
                
            except Exception as e:
                logger.warning(f"Cannot access input monitoring via Quartz: {e}")
                
                # Fallback: try a simple pynput test without listeners
                try:
                    from pynput import keyboard
                    # Just importing and checking if basic keyboard module works
                    logger.info("pynput keyboard module imported successfully")
                    logger.info("✅ Input Monitoring permission likely GRANTED")
                    return True
                    
                except Exception as e2:
                    logger.warning(f"pynput keyboard import failed: {e2}")
                    logger.warning("❌ Input Monitoring permission DENIED")
                    self._show_input_monitoring_permission_dialog()
                    return False
                
        except ImportError as e:
            logger.error(f"Required modules not available for input monitoring check: {e}")
            return False
    
    def _check_microphone_permission(self) -> bool:
        """Check microphone permission status."""
        logger.info("--- Checking Microphone Permission ---")
        logger.info("=== DETAILED MICROPHONE PERMISSION CHECK ===")
        
        try:
            # Method 1: Use AVFoundation to check permission status (most reliable)
            try:
                import sys
                import os
                
                # Try different import methods for AVFoundation
                logger.info("🔍 Attempting AVFoundation import...")
                
                # Method 1: Direct import
                try:
                    import AVFoundation
                    logger.info("✅ Direct AVFoundation import successful")
                except ImportError as e1:
                    logger.warning(f"Direct import failed: {e1}")
                    
                    # Method 2: Try with objc
                    try:
                        import objc
                        AVFoundation = objc.loadBundle('AVFoundation', globals(), bundle_path='/System/Library/Frameworks/AVFoundation.framework')
                        logger.info("✅ AVFoundation loaded via objc.loadBundle")
                    except Exception as e2:
                        logger.warning(f"objc.loadBundle failed: {e2}")
                        raise ImportError(f"All AVFoundation import methods failed: {e1}, {e2}")
                logger.info("✅ Successfully imported AVFoundation")
                logger.info(f"AVFoundation module: {AVFoundation}")
                logger.info(f"Has AVMediaTypeAudio: {hasattr(AVFoundation, 'AVMediaTypeAudio')}")
                logger.info(f"Has AVCaptureDevice: {hasattr(AVFoundation, 'AVCaptureDevice')}")
                
                # Check authorization status
                auth_status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
                    AVFoundation.AVMediaTypeAudio
                )
                
                logger.info(f"AVFoundation authorization status: {auth_status}")
                logger.info(f"Status meanings: 0=NotDetermined, 1=Restricted, 2=Denied, 3=Authorized")
                
                # Status codes: 0=NotDetermined, 1=Restricted, 2=Denied, 3=Authorized
                if auth_status == 3:  # Authorized
                    logger.info("✅ Microphone permission GRANTED via AVFoundation")
                    
                    # For built apps, also test actual microphone access to ensure it's really working
                    if getattr(sys, 'frozen', False):  # Only for built apps
                        logger.info("🔍 Built app detected - verifying actual microphone access...")
                        if self._verify_microphone_access_avfoundation():
                            logger.info("✅ Microphone access verified for built app")
                            return True
                        else:
                            logger.warning("❌ Microphone access verification failed for built app")
                            return self._request_microphone_permission_avfoundation()
                    
                    return True
                elif auth_status == 0:  # Not determined - request permission
                    logger.info("⚠️  Microphone permission not determined - requesting...")
                    return self._request_microphone_permission_avfoundation()
                elif auth_status == 2:  # Denied
                    logger.warning("❌ Microphone permission EXPLICITLY DENIED via AVFoundation")
                    self._show_microphone_permission_dialog()
                    return False
                elif auth_status == 1:  # Restricted
                    logger.warning("❌ Microphone permission RESTRICTED via AVFoundation")
                    self._show_microphone_permission_dialog()
                    return False
                else:
                    logger.warning(f"❓ Unknown microphone permission status: {auth_status}")
                    return False
                    
            except ImportError as e:
                logger.error(f"❌ AVFoundation import failed: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                logger.error(f"Exception args: {e.args}")
                
                # Try to debug the import issue
                try:
                    import sys
                    logger.info(f"Python path: {sys.path[:3]}...")
                    logger.info(f"Current working directory: {os.getcwd()}")
                    
                    # Try direct module location
                    import importlib.util
                    spec = importlib.util.find_spec("AVFoundation")
                    logger.info(f"AVFoundation spec: {spec}")
                    
                except Exception as debug_e:
                    logger.error(f"Debug import failed: {debug_e}")
                
                logger.warning("Falling back to PyAudio test (less reliable)")
                
                # Method 2: PyAudio test fallback (unreliable for permission checking)
                logger.info("⚠️  WARNING: PyAudio test may give false positives!")
                return self._test_microphone_with_pyaudio()
            
            except Exception as e:
                logger.error(f"❌ AVFoundation check failed with error: {e}")
                logger.warning("Falling back to PyAudio test")
                return self._test_microphone_with_pyaudio()
                
        except Exception as e:
            logger.error(f"❌ Critical error checking microphone permission: {e}")
            return False
    
    def _request_microphone_permission_avfoundation(self) -> bool:
        """Request microphone permission using AVFoundation."""
        logger.info("=== REQUESTING MICROPHONE PERMISSION VIA AVFOUNDATION ===")
        
        try:
            import objc
            from Foundation import NSRunLoop, NSDate, NSBundle
            
            # Log bundle info
            try:
                bundle = NSBundle.mainBundle()
                bundle_id = bundle.bundleIdentifier()
                logger.info(f"Requesting permission for bundle: {bundle_id}")
            except Exception as e:
                logger.warning(f"Could not get bundle info: {e}")
            
            # Use the same import method as in check function
            try:
                import AVFoundation
                logger.info("✅ Direct AVFoundation import successful in request function")
            except ImportError:
                logger.info("Direct import failed, trying objc.loadBundle...")
                AVFoundation = objc.loadBundle('AVFoundation', globals(), bundle_path='/System/Library/Frameworks/AVFoundation.framework')
                logger.info("✅ AVFoundation loaded via objc.loadBundle in request function")
            
            # Check current status first
            auth_status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
                AVFoundation.AVMediaTypeAudio
            )
            
            status_map = {
                0: "NotDetermined",
                1: "Restricted", 
                2: "Denied",
                3: "Authorized"
            }
            logger.info(f"Current microphone auth status: {status_map.get(auth_status, 'Unknown')} ({auth_status})")
            
            if auth_status == 3:  # Already authorized
                logger.info("✅ Microphone already authorized")
                return True
            elif auth_status == 2:  # Denied
                logger.warning("❌ Microphone access was previously denied")
                self._show_microphone_permission_dialog()
                return False
            elif auth_status == 1:  # Restricted
                logger.error("❌ Microphone access is restricted by system policy")
                return False
            
            logger.info("✅ Successfully imported AVFoundation, objc, and Foundation")
            logger.info("🔍 Requesting microphone permission via AVFoundation...")
            logger.info("⏳ This should trigger the macOS permission dialog...")
            
            # Use a completion block that works properly
            permission_granted = [False]  # Use list to modify from closure
            request_completed = [False]
            
            def completion_handler(granted):
                status_text = "Granted" if granted else "Denied"
                logger.info(f"🎯 Permission dialog result: {status_text}")
                permission_granted[0] = granted
                request_completed[0] = True
            
            # Request permission with proper completion handler
            logger.info("📞 Calling AVCaptureDevice.requestAccessForMediaType_completionHandler_...")
            AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                AVFoundation.AVMediaTypeAudio,
                completion_handler
            )
            logger.info("✅ Permission request call completed, waiting for callback...")
            
            # Wait for completion with proper runloop handling
            timeout = 0.0
            max_timeout = 30.0  # 30 second timeout
            logger.info(f"⏳ Waiting for permission dialog response (max {max_timeout}s)...")
            
            while not request_completed[0] and timeout < max_timeout:
                NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
                timeout += 0.1
                if timeout % 1.0 < 0.1:  # Log every second
                    logger.info(f"⏳ Still waiting... ({int(timeout)}s elapsed)")
            
            if request_completed[0]:
                granted = permission_granted[0]
                logger.info(f"🎯 Final microphone permission result: {'✅ GRANTED' if granted else '❌ DENIED'}")
                
                if not granted:
                    logger.warning("User denied microphone permission")
                    self._show_microphone_permission_dialog()
                else:
                    logger.info("User granted microphone permission!")
                    
                return granted
            else:
                logger.error(f"⏰ Microphone permission request timed out after {max_timeout}s")
                logger.error("This may indicate the permission dialog didn't appear")
                logger.info("Falling back to PyAudio test...")
                return self._test_microphone_with_pyaudio()
            
        except ImportError as e:
            logger.error(f"❌ Required modules not available: {e}")
            return self._test_microphone_with_pyaudio()
        except Exception as e:
            logger.error(f"❌ Error requesting microphone permission via AVFoundation: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            return self._test_microphone_with_pyaudio()
    
    def _test_microphone_with_pyaudio(self) -> bool:
        """Test microphone access using PyAudio."""
        logger.info("=== PYAUDIO MICROPHONE TEST (FALLBACK METHOD) ===")
        logger.info("⚠️  WARNING: This test may give false positives in development environments!")
        
        try:
            import pyaudio
            logger.info("✅ PyAudio imported successfully")
            
            audio = pyaudio.PyAudio()
            try:
                logger.info("🔍 Creating PyAudio test stream...")
                
                # Get default input device info
                try:
                    default_device = audio.get_default_input_device_info()
                    logger.info(f"Default input device: {default_device.get('name', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"Could not get default input device info: {e}")
                
                # Try to open microphone stream
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,  # Use lower sample rate for compatibility
                    input=True,
                    frames_per_buffer=1024
                )
                
                logger.info("✅ PyAudio stream opened successfully")
                
                # Try to read some data
                data = stream.read(1024, exception_on_overflow=False)
                logger.info(f"✅ Successfully read {len(data)} bytes from microphone")
                
                # Check if we actually got audio data (not just silence)
                import struct
                audio_data = struct.unpack('h' * (len(data) // 2), data)
                max_amplitude = max(abs(x) for x in audio_data) if audio_data else 0
                logger.info(f"Max audio amplitude: {max_amplitude}")
                
                stream.stop_stream()
                stream.close()
                
                logger.info("✅ Microphone permission LIKELY GRANTED via PyAudio test")
                logger.warning("⚠️  NOTE: This may be a false positive in development environments!")
                return True
                
            except Exception as e:
                logger.warning(f"❌ PyAudio microphone test failed: {e}")
                logger.warning("❌ Microphone permission DENIED - PyAudio test failed")
                self._show_microphone_permission_dialog()
                return False
            finally:
                audio.terminate()
                
        except ImportError as e:
            logger.error(f"❌ PyAudio not available: {e}")
            return False
    
    def _verify_microphone_access_avfoundation(self) -> bool:
        """Verify actual microphone access using AVFoundation capture session."""
        logger.info("=== VERIFYING ACTUAL MICROPHONE ACCESS ===")
        
        try:
            # Use same import method
            try:
                import AVFoundation
            except ImportError:
                import objc
                AVFoundation = objc.loadBundle('AVFoundation', globals(), bundle_path='/System/Library/Frameworks/AVFoundation.framework')
            
            logger.info("🔍 Creating AVCaptureSession to test actual microphone access...")
            
            # Create capture session to test real access
            session = AVFoundation.AVCaptureSession.alloc().init()
            
            # Get default audio device
            device = AVFoundation.AVCaptureDevice.defaultDeviceWithMediaType_(AVFoundation.AVMediaTypeAudio)
            if not device:
                logger.warning("❌ No audio capture device found")
                return False
            
            logger.info(f"Found audio device: {device.localizedName()}")
            
            # Create device input
            try:
                device_input = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)
                if not device_input:
                    logger.warning("❌ Could not create device input")
                    return False
                
                logger.info("✅ Created device input successfully")
                
                # Try to add input to session
                if session.canAddInput_(device_input):
                    session.addInput_(device_input)
                    logger.info("✅ Added input to capture session")
                    
                    # Start session briefly to test access
                    session.startRunning()
                    logger.info("✅ Capture session started successfully")
                    
                    # Stop immediately
                    session.stopRunning()
                    logger.info("✅ Microphone access verification successful")
                    return True
                else:
                    logger.warning("❌ Cannot add input to capture session")
                    return False
                    
            except Exception as e:
                logger.warning(f"❌ Device input creation failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Microphone verification failed: {e}")
            return False
    
    def _show_accessibility_permission_dialog(self):
        """Show accessibility permission dialog."""
        logger.info("Showing accessibility permission dialog...")
        self._show_permission_dialog(
            "Accessibility",
            "Speechy needs Accessibility permissions for global hotkeys and auto-typing.\n\nPlease enable Speechy in:\nSystem Settings > Privacy & Security > Accessibility",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        )
    
    def _show_input_monitoring_permission_dialog(self):
        """Show input monitoring permission dialog."""
        logger.info("Showing input monitoring permission dialog...")
        self._show_permission_dialog(
            "Input Monitoring",
            "Speechy needs Input Monitoring permissions for global hotkeys.\n\nPlease enable Speechy in:\nSystem Settings > Privacy & Security > Input Monitoring",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"
        )
    
    def _show_microphone_permission_dialog(self):
        """Show microphone permission dialog."""
        logger.info("Showing microphone permission dialog...")
        self._show_permission_dialog(
            "Microphone",
            "Speechy needs Microphone access to record your voice.\n\nPlease enable Speechy in:\nSystem Settings > Privacy & Security > Microphone",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
        )
    
    def _show_permission_dialog(self, permission_type: str, message: str, settings_url: str):
        """Show a permission dialog with option to open settings."""
        try:
            script = f'''
            tell application "System Events"
                display dialog "{message}
                
The app will open System Settings for you." buttons {{"Open System Settings", "Continue"}} default button "Open System Settings" with title "Permission Required: {permission_type}" with icon caution
                
                if button returned of result is "Open System Settings" then
                    do shell script "open '{settings_url}'"
                end if
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, check=False)
            logger.info(f"Permission dialog result: {result.stdout.strip()}")
            
        except Exception as e:
            logger.error(f"Error showing {permission_type} permission dialog: {e}")