# Speechy Permission Management System

This document provides a comprehensive overview of how Speechy handles macOS permissions for microphone access, accessibility features, and keyboard shortcuts (input monitoring).

## Overview

Speechy requires three critical macOS permissions to function properly:

1. **Microphone** - For voice recording and transcription
2. **Accessibility** - For auto-typing functionality and some hotkey operations
3. **Input Monitoring** - For global hotkey detection (F9, etc.)

## Architecture Components

### 1. PermissionManager Class (`permission_manager.py`)

The `PermissionManager` class is the central component that handles all permission checking and requesting. It provides:

- **Comprehensive permission checking** using multiple detection methods
- **Native macOS API integration** (AVFoundation, ApplicationServices, Quartz)
- **Fallback mechanisms** when primary methods fail
- **User-friendly dialog prompts** with direct links to System Settings
- **Detailed logging** for debugging permission issues

#### Key Methods:

```python
def check_all_permissions(self) -> Dict[str, bool]:
    """Check all required permissions and return status."""
    # Returns: {'microphone': bool, 'accessibility': bool, 'input_monitoring': bool}

def _check_microphone_permission(self) -> bool:
    """Check microphone permission using AVFoundation API."""
    
def _check_accessibility_permission(self) -> bool:
    """Check accessibility permission using ApplicationServices."""
    
def _check_input_monitoring_permission(self) -> bool:
    """Check input monitoring permission using Quartz framework."""
```

### 2. Permission Declaration Files (Plists)

#### Info.plist - Permission Usage Descriptions
Located at `voice-assistant/Info.plist`, this file declares why the app needs each permission:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Speechy needs microphone access to record your voice for speech-to-text transcription and AI assistance.</string>

<key>NSAppleEventsUsageDescription</key>
<string>Speechy needs to control other applications to enable auto-typing functionality and global hotkey support.</string>

<key>NSInputMonitoringUsageDescription</key>
<string>Speechy needs Input Monitoring access to detect global hotkeys (like F9) for hands-free voice recording control.</string>

<key>NSSystemAdministrationUsageDescription</key>
<string>Speechy needs system administration access for advanced input monitoring and accessibility features.</string>
```

#### entitlements.plist - Security Entitlements
Located at `voice-assistant/entitlements.plist`, this file specifies security entitlements:

```xml
<key>com.apple.security.device.microphone</key>
<true/>

<key>com.apple.security.device.audio-input</key>
<true/>

<key>com.apple.security.automation.apple-events</key>
<true/>

<key>com.apple.security.device.usb</key>
<true/>
```

## Permission Checking Logic Flow

### 1. Microphone Permission

The microphone permission uses a sophisticated multi-tier approach:

#### Primary Method: AVFoundation API
```python
# Import AVFoundation framework
import AVFoundation

# Check authorization status
auth_status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
    AVFoundation.AVMediaTypeAudio
)

# Status codes:
# 0 = NotDetermined (need to request)
# 1 = Restricted 
# 2 = Denied
# 3 = Authorized
```

#### Permission Request Process:
```python
def _request_microphone_permission_avfoundation(self) -> bool:
    """Request microphone permission using AVFoundation."""
    
    permission_granted = [False]
    request_completed = [False]
    
    def completion_handler(granted):
        permission_granted[0] = granted
        request_completed[0] = True
    
    # Request permission with completion handler
    AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
        AVFoundation.AVMediaTypeAudio,
        completion_handler
    )
    
    # Wait for user response with timeout
    while not request_completed[0] and timeout < max_timeout:
        NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
```

#### Fallback Method: PyAudio Test
If AVFoundation fails, the system falls back to a PyAudio-based test:

```python
def _test_microphone_with_pyaudio(self) -> bool:
    """Test microphone access using PyAudio."""
    audio = pyaudio.PyAudio()
    
    # Try to open microphone stream
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    # Test reading audio data
    data = stream.read(1024, exception_on_overflow=False)
    return len(data) > 0
```

### 2. Accessibility Permission

Accessibility permission checking uses ApplicationServices framework:

#### Primary Method: ApplicationServices
```python
import ApplicationServices

# Check if process is trusted for accessibility
trusted = ApplicationServices.AXIsProcessTrusted()

if trusted:
    return True  # Permission granted
else:
    # Show permission dialog and return False
    self._show_accessibility_permission_dialog()
    return False
```

#### Fallback Method: AppleScript Test
```python
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

result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
```

### 3. Input Monitoring Permission

Input monitoring uses the Quartz framework:

#### Primary Method: Quartz Event Source
```python
import Quartz

# Try to get current modifier flags
event_flags = Quartz.CGEventSourceFlagsState(
    Quartz.kCGEventSourceStateCombinedSessionState
)

# If this succeeds, we have input monitoring permission
return True
```

#### Fallback Method: pynput Test
```python
from pynput import keyboard

# Test if pynput keyboard module works
# Success indicates input monitoring permission
return True
```

## Permission Dialog System

When permissions are missing, the system shows native macOS dialogs with direct links to System Settings:

```python
def _show_permission_dialog(self, permission_type: str, message: str, settings_url: str):
    """Show a permission dialog with option to open settings."""
    script = f'''
    tell application "System Events"
        display dialog "{message}
        
The app will open System Settings for you." buttons {{"Open System Settings", "Continue"}} default button "Open System Settings" with title "Permission Required: {permission_type}" with icon caution
        
        if button returned of result is "Open System Settings" then
            do shell script "open '{settings_url}'"
        end if
    end tell
    '''
```

### Permission-Specific Settings URLs:
- **Accessibility**: `x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility`
- **Input Monitoring**: `x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent`
- **Microphone**: `x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone`

## Application Integration

### 1. Startup Integration (`application_manager.py`)

The permission system is integrated into the application startup process:

```python
def initialize_voice_assistant(self):
    """Initialize the voice assistant components."""
    from permission_manager import PermissionManager
    
    permission_manager = PermissionManager()
    permissions = permission_manager.check_all_permissions()
    
    # Log permission status
    if permissions['accessibility']:
        logger.info("✅ Accessibility permissions ready")
    else:
        logger.warning("⚠️  Accessibility permissions missing")
    
    # Continue with app initialization
```

### 2. GUI Integration (`gui.py`)

The GUI includes a dedicated permissions tab with visual status indicators:

```python
class PermissionStatusWidget(QWidget):
    """Widget to display and manage macOS permission status."""
    
    def init_ui(self):
        # Create permission status labels with ✅/❌ indicators
        # Add "Open Settings" buttons for each permission
        # Implement "Refresh Status" functionality
```

### 3. Real-time Permission Monitoring

The GUI provides:
- **Visual status indicators** (✅/❌) for each permission
- **"Open Settings" buttons** that launch System Settings to the correct pane
- **"Refresh Status" button** to re-check permissions after changes
- **Real-time updates** when permissions change

## Build Process Integration

### PyInstaller Configuration (`speechy.spec`)

The build process integrates both plist files:

```python
# In speechy.spec
app = BUNDLE(
    exe,
    name='Speechy.app',
    icon='speechy_icon.icns',
    bundle_identifier='com.chrisventer.speechy',
    info_plist={
        # Info.plist contents merged here
        'NSMicrophoneUsageDescription': 'Speechy needs microphone access...',
        'NSAppleEventsUsageDescription': 'Speechy needs to control other applications...',
        # ... other keys
    },
    entitlements_file='entitlements.plist'  # Security entitlements
)
```

### Build Command

```bash
# Install PyInstaller
pip install pyinstaller

# Build with configured spec file
pyinstaller speechy.spec

# The resulting .app bundle includes both plist files
```

## Error Handling and Logging

The permission system includes comprehensive error handling:

```python
def check_all_permissions(self) -> Dict[str, bool]:
    logger.info("=" * 60)
    logger.info("=== STARTING COMPREHENSIVE PERMISSION CHECK ===")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    
    # Check each permission with detailed logging
    self.permissions['accessibility'] = self._check_accessibility_permission()
    self.permissions['input_monitoring'] = self._check_input_monitoring_permission()
    self.permissions['microphone'] = self._check_microphone_permission()
    
    # Log summary
    for perm_type, status in self.permissions.items():
        emoji = "✅" if status else "❌"
        logger.info(f"{emoji} {perm_type.upper()}: {'GRANTED' if status else 'DENIED'}")
    
    return self.permissions.copy()
```

## Best Practices

1. **Multiple Detection Methods**: Each permission type has primary and fallback detection methods
2. **Graceful Degradation**: App continues to function with reduced capabilities when permissions are missing
3. **User-Friendly Guidance**: Clear dialogs with direct links to System Settings
4. **Comprehensive Logging**: Detailed logs help debug permission issues
5. **Real-time Updates**: GUI reflects permission changes immediately
6. **Proper Entitlements**: Both Info.plist and entitlements.plist are properly configured for the build process

## Troubleshooting

Common issues and solutions:

1. **AVFoundation Import Fails**: Falls back to PyAudio test
2. **Permission Dialog Doesn't Appear**: Logs timeout and suggests manual settings check
3. **Built App vs Script Differences**: Different permission handling for development vs production
4. **Framework Loading Issues**: Multiple import methods with proper error handling

This comprehensive system ensures reliable permission management across different macOS versions and deployment scenarios.