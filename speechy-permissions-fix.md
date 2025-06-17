# Speechy macOS Permissions Fix Guide

## Problem Summary
The Speechy voice assistant application works correctly in the VS Code development environment but fails to request microphone permissions when built with PyInstaller. This prevents voice input functionality in the distributed `.app` bundle.

## Root Causes Analysis

### 1. **Code Signing and Notarization**
- macOS requires apps to be properly code-signed to request certain permissions
- Unsigned apps are treated as untrusted and permission APIs may not function

### 2. **Info.plist Integration Issues**
- PyInstaller sometimes fails to properly embed Info.plist values in the final app bundle
- Missing or incorrect usage descriptions prevent permission dialogs from appearing

### 3. **Entitlements Not Being Applied**
- Entitlements must be applied during the code signing process
- Simply including them in the PyInstaller spec may not be sufficient

## Solutions

### Solution 1: Proper Code Signing (Most Important)

#### With Developer ID Certificate:
```bash
# After building with PyInstaller
pyinstaller speechy.spec

# Sign the app with your Developer ID (replace with your identity)
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name (TEAMID)" \
    --options runtime \
    --entitlements entitlements.plist \
    dist/Speechy.app

# Verify the signature
codesign --verify --verbose dist/Speechy.app

# Check if entitlements were applied
codesign -d --entitlements - dist/Speechy.app
```

#### For Testing (Ad-hoc Signing):
```bash
# Use ad-hoc signing if you don't have a Developer ID
codesign --deep --force --verify --verbose --sign - \
    --options runtime \
    --entitlements entitlements.plist \
    dist/Speechy.app
```

### Solution 2: Update Your entitlements.plist

Create or update `entitlements.plist` with all required permissions:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.device.microphone</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.device.usb</key>
    <true/>
</dict>
</plist>
```

### Solution 3: Modify speechy.spec

Update your `speechy.spec` file to ensure proper Info.plist integration:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['speechy.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('speechy_icon.icns', '.'),
        # Add any other data files here
    ],
    hiddenimports=[
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'AVFoundation',
        'ApplicationServices',
        'Quartz',
        'AppKit',
        'Foundation',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Speechy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='Speechy.app',
    icon='speechy_icon.icns',
    bundle_identifier='com.chrisventer.speechy',
    info_plist={
        'CFBundleName': 'Speechy',
        'CFBundleDisplayName': 'Speechy',
        'CFBundleIdentifier': 'com.chrisventer.speechy',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': 'Speechy',
        'CFBundleIconFile': 'speechy_icon.icns',
        'NSMicrophoneUsageDescription': 'Speechy needs microphone access to record your voice for speech-to-text transcription and AI assistance.',
        'NSAppleEventsUsageDescription': 'Speechy needs to control other applications to enable auto-typing functionality and global hotkey support.',
        'NSInputMonitoringUsageDescription': 'Speechy needs Input Monitoring access to detect global hotkeys (like F9) for hands-free voice recording control.',
        'NSSystemAdministrationUsageDescription': 'Speechy needs system administration access for advanced input monitoring and accessibility features.',
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.productivity',
    },
)
```

### Solution 4: Complete Build Script

Create `build_app.sh`:

```bash
#!/bin/bash

# Exit on error
set -e

echo "🔨 Building Speechy..."

# Clean previous builds
echo "📦 Cleaning previous builds..."
rm -rf build dist

# Build with PyInstaller
echo "🏗️  Running PyInstaller..."
pyinstaller speechy.spec

# Fix permissions on the app bundle
echo "🔧 Setting permissions..."
chmod -R 755 dist/Speechy.app

# Check if we have a Developer ID
IDENTITY="Developer ID Application: Your Name (TEAMID)"
if security find-identity -p codesigning | grep -q "$IDENTITY"; then
    echo "✅ Found Developer ID certificate"
    SIGN_IDENTITY="$IDENTITY"
else
    echo "⚠️  No Developer ID found, using ad-hoc signing"
    SIGN_IDENTITY="-"
fi

# Sign the app with entitlements
echo "✍️  Signing app..."
codesign --deep --force --verify --verbose \
    --sign "$SIGN_IDENTITY" \
    --options runtime \
    --entitlements entitlements.plist \
    dist/Speechy.app

# Verify the signature
echo "🔍 Verifying signature..."
codesign --verify --verbose dist/Speechy.app

echo "📋 Checking entitlements..."
codesign -d --entitlements - dist/Speechy.app

echo "✅ Build complete! App is at: dist/Speechy.app"

# Optional: Create a DMG for distribution
read -p "Create DMG for distribution? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💿 Creating DMG..."
    create-dmg \
        --volname "Speechy" \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "Speechy.app" 175 120 \
        --hide-extension "Speechy.app" \
        --app-drop-link 425 120 \
        "Speechy.dmg" \
        "dist/"
    echo "✅ DMG created: Speechy.dmg"
fi
```

Make it executable:
```bash
chmod +x build_app.sh
```

### Solution 5: Enhanced Permission Manager Debugging

Add this debugging code to your `permission_manager.py`:

```python
import platform
import sys
from Foundation import NSBundle
import logging

logger = logging.getLogger(__name__)

class PermissionManager:
    def __init__(self):
        self._log_environment()
    
    def _log_environment(self):
        """Log environment information for debugging."""
        logger.info("=" * 60)
        logger.info("ENVIRONMENT INFORMATION")
        logger.info("=" * 60)
        logger.info(f"Python: {sys.version}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"macOS Version: {platform.mac_ver()[0]}")
        
        # Check if running as app bundle
        bundle = NSBundle.mainBundle()
        logger.info(f"Bundle ID: {bundle.bundleIdentifier()}")
        logger.info(f"Bundle Path: {bundle.bundlePath()}")
        logger.info(f"Executable Path: {bundle.executablePath()}")
        logger.info(f"Is App Bundle: {'Speechy.app' in str(bundle.bundlePath())}")
        
        # Check Info.plist values
        info_dict = bundle.infoDictionary()
        if info_dict:
            logger.info("Info.plist Usage Descriptions:")
            for key in ['NSMicrophoneUsageDescription', 
                       'NSAppleEventsUsageDescription',
                       'NSInputMonitoringUsageDescription']:
                value = info_dict.get(key, "NOT FOUND")
                logger.info(f"  {key}: {value[:50]}...")
        logger.info("=" * 60)

    def _request_microphone_permission_avfoundation(self) -> bool:
        """Request microphone permission using AVFoundation."""
        try:
            import AVFoundation
            from Foundation import NSRunLoop, NSDate
            
            # Log bundle info
            bundle = NSBundle.mainBundle()
            logger.info(f"Requesting permission for bundle: {bundle.bundleIdentifier()}")
            
            # Check current status
            auth_status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
                AVFoundation.AVMediaTypeAudio
            )
            
            status_map = {
                0: "NotDetermined",
                1: "Restricted",
                2: "Denied",
                3: "Authorized"
            }
            logger.info(f"Current microphone auth status: {status_map.get(auth_status, 'Unknown')}")
            
            if auth_status == 3:  # Already authorized
                return True
            elif auth_status == 2:  # Denied
                logger.warning("Microphone access was previously denied")
                self._show_microphone_permission_dialog()
                return False
            elif auth_status == 1:  # Restricted
                logger.error("Microphone access is restricted by system policy")
                return False
                
            # Request permission
            logger.info("Requesting microphone permission...")
            
            permission_granted = [False]
            request_completed = [False]
            
            def completion_handler(granted):
                logger.info(f"Permission dialog result: {'Granted' if granted else 'Denied'}")
                permission_granted[0] = granted
                request_completed[0] = True
            
            # Request permission
            AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                AVFoundation.AVMediaTypeAudio,
                completion_handler
            )
            
            # Wait for response with timeout
            timeout = 0
            while not request_completed[0] and timeout < 30:
                NSRunLoop.currentRunLoop().runUntilDate_(
                    NSDate.dateWithTimeIntervalSinceNow_(0.1)
                )
                timeout += 0.1
            
            if not request_completed[0]:
                logger.error("Permission request timed out after 30 seconds")
                return False
                
            return permission_granted[0]
            
        except Exception as e:
            logger.error(f"Failed to request microphone permission: {e}", exc_info=True)
            return False
```

### Solution 6: Reset Permissions for Testing

Create `reset_permissions.sh`:

```bash
#!/bin/bash

echo "🔄 Resetting permissions for Speechy..."

# Reset specific permissions
tccutil reset Microphone com.chrisventer.speechy
tccutil reset Accessibility com.chrisventer.speechy
tccutil reset ListenEvent com.chrisventer.speechy
tccutil reset AppleEvents com.chrisventer.speechy

# Alternative: Reset all permissions for the app
# tccutil reset All com.chrisventer.speechy

echo "✅ Permissions reset. The app will ask for permissions again on next launch."
```

### Solution 7: Alternative Build Method with py2app

If PyInstaller continues to have issues, try py2app:

```bash
pip install py2app
```

Create `setup.py`:

```python
from setuptools import setup

APP = ['speechy.py']
DATA_FILES = ['speechy_icon.icns']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'speechy_icon.icns',
    'plist': {
        'CFBundleName': 'Speechy',
        'CFBundleDisplayName': 'Speechy',
        'CFBundleIdentifier': 'com.chrisventer.speechy',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSMicrophoneUsageDescription': 'Speechy needs microphone access to record your voice for speech-to-text transcription and AI assistance.',
        'NSAppleEventsUsageDescription': 'Speechy needs to control other applications to enable auto-typing functionality and global hotkey support.',
        'NSInputMonitoringUsageDescription': 'Speechy needs Input Monitoring access to detect global hotkeys (like F9) for hands-free voice recording control.',
        'NSSystemAdministrationUsageDescription': 'Speechy needs system administration access for advanced input monitoring and accessibility features.',
        'LSMinimumSystemVersion': '10.15.0',
    },
    'packages': ['pynput', 'pyaudio', 'speech_recognition', 'openai'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

Build with:
```bash
python setup.py py2app
```

## Troubleshooting Checklist

1. **Verify Code Signing**
   ```bash
   codesign -dvvv dist/Speechy.app
   ```

2. **Check Entitlements**
   ```bash
   codesign -d --entitlements - dist/Speechy.app
   ```

3. **Verify Info.plist**
   ```bash
   defaults read dist/Speechy.app/Contents/Info.plist
   ```

4. **Test in Console**
   - Open Console.app
   - Filter for "Speechy" or "tccd"
   - Look for permission-related errors

5. **Check System Logs**
   ```bash
   log show --predicate 'subsystem == "com.apple.TCC"' --last 5m
   ```

## Quick Start Guide

1. **Update your files**:
   - Replace `entitlements.plist` with the enhanced version
   - Update `speechy.spec` with the complete configuration
   - Add debugging to `permission_manager.py`

2. **Create build script**:
   ```bash
   # Save build_app.sh and make executable
   chmod +x build_app.sh
   ```

3. **Build and sign**:
   ```bash
   ./build_app.sh
   ```

4. **Test**:
   ```bash
   # Reset permissions first
   ./reset_permissions.sh
   
   # Run the app
   open dist/Speechy.app
   ```

## Expected Outcome

After implementing these fixes, your Speechy app should:
- Properly request microphone permission on first launch
- Show the permission dialog with your custom usage description
- Successfully access the microphone after permission is granted
- Work identically to the development environment

## Additional Resources

- [Apple's Code Signing Guide](https://developer.apple.com/documentation/security/code_signing_services)
- [Notarizing macOS Software](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [TCC (Transparency, Consent, and Control) Documentation](https://developer.apple.com/documentation/security/transparency_consent_and_control)
- [PyInstaller macOS Bundle Documentation](https://pyinstaller.readthedocs.io/en/stable/spec-files.html#spec-file-options-for-a-mac-os-x-bundle)

## Support

If you continue to experience issues after implementing these solutions:

1. Check the Console.app logs for TCC-related errors
2. Ensure your macOS version supports the requested permissions
3. Try building on a different macOS version
4. Consider using a Developer ID certificate for production builds
5. Test on a clean macOS installation or different machine

Remember: The key to fixing permission issues is almost always proper code signing with the correct entitlements.