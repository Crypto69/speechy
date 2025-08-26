# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment Setup

This is **Speechy - Your AI Voice Assistant**, a comprehensive voice-to-text application using OpenAI Whisper and Ollama with auto-typing capabilities. Development requires:

```bash
# Activate conda environment
conda activate speechy

# Install dependencies  
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve

# Run the application
python main.py
```

## ⚠️ CRITICAL: Hotkey Stability Information

**WORKING BASELINE: Commit 851bb1d**
- ✅ Global hotkeys (F9) work perfectly 
- ✅ All functionality confirmed working: recording, transcription, auto-typing, LLM processing
- ✅ All macOS permissions properly detected and working
- 🔒 This commit is the STABLE BASELINE - never modify without testing hotkeys

**Known Hotkey Breaking Patterns:**
- ⚠️ Timing measurements (`time.time()`) during component initialization interfere with pynput
- ❌ Splash screen implementations CONFIRMED to break hotkeys (QSplashScreen causes Qt event loop interference)
- ⚠️ Any changes to application startup sequence must be tested for hotkey compatibility
- ⚠️ GUI components shown before hotkey manager initialization can cause timing conflicts

**Testing Hotkeys After Changes:**
1. Run application: `python main.py` 
2. Wait for "Hotkey listener started for: f9" log message
3. Press F9 to start recording (should see "Hotkey activated: f9" in logs)
4. Speak some test words
5. Press F9 again to stop recording
6. Verify transcription appears and auto-typing works
7. ❌ If hotkeys don't work, immediately revert changes

## Essential Commands

**Run Application:**
```bash
python main.py
```

**Test Dependencies:**
```bash
python -c "import faster_whisper, pyaudio, PyQt5; print('All imports successful')"
```

**Check Ollama Connection:**
```bash
curl http://localhost:11434/api/tags
```

**List Audio Devices (for debugging):**
```bash
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
"
```

**Install macOS Dependencies:**
```bash
# Install required PyObjC frameworks for permission checking
pip install pyobjc-framework-Cocoa pyobjc-framework-AVFoundation pyobjc-framework-Quartz pyobjc-framework-Foundation pyobjc-framework-ApplicationServices
```

**Build Executable (Automated - Recommended):**
```bash
# Automated build with code signing and verification
./build_app.sh
```

**Build Executable (Manual):**
```bash
pip install pyinstaller
# Use the configured spec file (includes Info.plist and entitlements for permissions)
pyinstaller speechy.spec

# Manual code signing (required for permissions to work)
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Christian Venter (4R94388LH8)" \
    --options runtime \
    --entitlements voice-assistant/entitlements.plist \
    dist/Speechy.app
```

**Alternative Build Method (py2app):**
```bash
pip install py2app
python setup.py py2app
# Then sign with codesign as above
```

**macOS Permissions:**
The app requires three permissions on macOS:
1. **Input Monitoring** - For global hotkeys (F9, etc.)
2. **Accessibility** - For auto-typing functionality  
3. **Microphone** - For voice recording

**Permission Management:**
- The app includes a dedicated "🔐 Permissions" tab with visual status indicators
- Real-time permission checking with ✅/❌ status display
- Direct links to System Settings for each permission type
- Automatic permission request on first launch using proper macOS APIs
- Built with proper entitlements file and code signing for microphone access
- Enhanced debugging with environment and bundle information logging

**Permission Testing & Debugging:**
```bash
# Reset all permissions for fresh testing
./reset_permissions.sh

# Check what certificates are available
security find-identity -p codesigning

# Monitor permission requests in real-time
log show --predicate 'subsystem == "com.apple.TCC"' --last 5m

# Check Console.app for permission-related errors
# Filter for "Speechy" or "tccd"
```

**First Launch:**
1. App will automatically request Input Monitoring permission (approve this)
2. App will show Permissions tab if any permissions are missing  
3. Use "Open Settings" buttons to grant remaining permissions
4. Use "Refresh Status" to update permission display
5. All permissions should show ✅ when properly granted

**Troubleshooting Permissions:**
- **Built app won't request permissions**: Ensure app is properly code signed with entitlements
- **Development vs Built differences**: Check bundle ID and signing status
- **Permission dialog doesn't appear**: Check Console.app for TCC errors
- **Reset for testing**: Use `./reset_permissions.sh` script

## Architecture Overview

The application follows an event-driven architecture with these key components:

**Core Workflow:**
1. `HotkeyManager` (in main.py) detects global hotkey presses
2. `AudioHandler` captures microphone input to temporary WAV files
3. `WhisperTranscriber` processes audio files locally using faster-whisper
4. `OllamaClient` sends transcriptions to local Ollama server for AI responses
5. `AutoTyper` types corrected text directly at cursor position (optional)
6. `VoiceAssistantGUI` displays results and provides configuration interface

**Key Classes and Responsibilities:**

- **`VoiceAssistant`** (main.py): Central coordinator that orchestrates all components
- **`HotkeyManager`** (main.py): Global hotkey detection using pynput, supports F-keys and modifier combinations
- **`AudioHandler`** (audio_handler.py): Real-time audio capture with PyAudio, includes level monitoring and temporary file management
- **`WhisperTranscriber`** (transcriber.py): Local Whisper model loading and transcription with device optimization (CPU/GPU)
- **`OllamaClient`** (llm_client.py): HTTP client for Ollama API with model management and error handling
- **`AutoTyper`** (auto_typer.py): Automatic typing at cursor position with app exclusions and customizable delays
- **`VoiceAssistantGUI`** (gui.py): PyQt5 interface with system tray, tabbed interface, visual recording indicators, and custom about dialog
- **`PermissionManager`** (permission_manager.py): Comprehensive macOS permission checking and requesting with multiple detection methods and detailed logging
- **`Config`** (config.py): JSON-based configuration management with runtime updates

**Threading Model:**
- Main thread runs PyQt5 GUI event loop
- Separate threads for: audio recording, Whisper transcription, Ollama API calls, model loading, auto-typing
- Qt signals/slots coordinate between threads and GUI updates

**Configuration System:**
- `config.json` stores all settings with defaults in `Config.DEFAULT_CONFIG`
- Runtime configuration changes via GUI settings tab
- Settings automatically saved and propagated to components

**State Management:**
- Recording state managed in `VoiceAssistant` class
- GUI state synchronized via Qt signals
- Audio level monitoring with real-time callbacks
- Temporary file cleanup after processing

## Key Configuration Points

**Model Selection:**
- Whisper models: tiny (fastest) → base (recommended) → small → medium → large (most accurate)
- Ollama models: llama3.2:1b (fastest) → llama3.2:3b (recommended) → llama3.1:8b (best quality)

**Audio Settings:**
- Sample rate: 16000 Hz (default), can be adjusted for quality/performance tradeoffs
- Device selection: null for default, or specific device index from audio device enumeration

**Hotkey Configuration:**
- Supports F-keys (f5, f6, f9, f10, f11, f12) and modifier combinations (ctrl+space, alt+space)
- Parsed in `HotkeyManager.parse_hotkey()` method

**Auto-Typing Configuration:**
- Three modes: "raw" (original transcription), "corrected" (AI-improved), "both" (both texts)
- Configurable typing delay and speed
- Application exclusion list to prevent typing in unwanted apps
- Cross-platform support using pynput

## Common Development Patterns

**Adding New Models:**
- Extend `transcriber.py` for new speech-to-text services
- Extend `llm_client.py` for different LLM APIs
- Update `Config.DEFAULT_CONFIG` for new model options

**GUI Extensions:**
- Add new tabs in `VoiceAssistantGUI.create_*_tab()` methods
- Use Qt signals for thread-safe GUI updates
- Follow existing dark theme styling patterns

**Error Handling:**
- All components use Python logging with structured log messages
- GUI shows user-friendly status messages via `statusBar()`
- Network errors handled gracefully with fallback behaviors

## Platform-Specific Notes

**macOS:**
- Requires three permissions: Microphone, Accessibility, Input Monitoring
- PyAudio dependency: `brew install portaudio`
- Code signing required for permission dialogs to work properly
- Uses AVFoundation, ApplicationServices, and Quartz frameworks for permission checking

**Linux:**
- May need sudo for global hotkey access
- PyAudio dependency: `sudo apt-get install portaudio19-dev`

**Windows:**
- May need administrator privileges for hotkeys
- PyAudio installation sometimes requires pipwin

## Build System Files

**Core Build Files:**
- `speechy.spec` - PyInstaller configuration with hidden imports and bundle settings
- `build_app.sh` - Automated build script with code signing and verification
- `setup.py` - Alternative py2app build configuration
- `voice-assistant/entitlements.plist` - Security entitlements for code signing
- `voice-assistant/Info.plist` - App bundle metadata and permission usage descriptions

**Testing & Debugging:**
- `reset_permissions.sh` - Reset app permissions for testing
- `PERMISSION_MANAGEMENT_SUMMARY.md` - Comprehensive permission system documentation

**Key Build Features:**
- Automatic Developer ID certificate detection
- Fallback to ad-hoc signing for development
- Entitlements integration for macOS permissions
- Bundle verification and signature checking
- Optional DMG creation for distribution