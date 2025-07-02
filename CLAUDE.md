# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Speechy - Your AI Voice Assistant** is a macOS desktop application that combines OpenAI Whisper for local speech-to-text transcription with Ollama LLMs for intelligent text processing and auto-typing capabilities. The project focuses on privacy-first local processing and seamless macOS integration.

## Essential Commands

**Development Environment Setup:**
```bash
# Activate conda environment
conda activate speechy
cd voice-assistant

# Install all dependencies
pip install -r requirements.txt

# Install macOS-specific frameworks
pip install pyobjc-framework-Cocoa pyobjc-framework-AVFoundation pyobjc-framework-Quartz pyobjc-framework-Foundation pyobjc-framework-ApplicationServices

# Ensure Ollama is running
ollama serve

# Run the application
python main.py
```

**Dependency Testing:**
```bash
# Verify core imports work
python -c "import faster_whisper, pyaudio, PyQt5; print('All imports successful')"

# Check Ollama connection
curl http://localhost:11434/api/tags

# List available audio devices (debugging)
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
"
```

**Build Commands:**
```bash
# Automated build with code signing (recommended)
./build_app.sh

# Manual PyInstaller build
pip install pyinstaller
pyinstaller speechy.spec

# Alternative py2app build
pip install py2app
python setup.py py2app

# Manual code signing (required for permissions)
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Christian Venter (4R94388LH8)" \
    --options runtime \
    --entitlements voice-assistant/entitlements.plist \
    dist/Speechy.app
```

**Permission Management:**
```bash
# Reset all permissions for testing
./reset_permissions.sh

# Check available certificates
security find-identity -p codesigning

# Monitor permission requests in real-time
log show --predicate 'subsystem == "com.apple.TCC"' --last 5m
```

## Architecture Overview

### Core Application Flow
1. **main.py** → **application_manager.py** - Entry point and lifecycle management
2. **application_manager.py** - Initializes components and manages startup behavior (show/hide main window)
3. **voice_assistant.py** - Central coordinator orchestrating all components
4. **hotkey_manager.py** - Global hotkey detection (F9) using pynput
5. **audio_handler.py** - Microphone capture with PyAudio
6. **transcriber.py** - Local Whisper processing with faster-whisper
7. **llm_client.py** - Ollama API integration for text enhancement
8. **auto_typer.py** - Automatic typing at cursor position
9. **gui.py** - PyQt5 interface with system tray integration

### Threading Architecture
- **Main Thread**: PyQt5 GUI event loop and system tray
- **Audio Thread**: Real-time microphone capture and level monitoring
- **Transcription Thread**: Whisper model processing (CPU/GPU optimized)
- **LLM Thread**: Ollama API calls for text correction
- **Auto-typing Thread**: Cursor position typing with configurable delays
- **Model Loading Thread**: Asynchronous model initialization with progress updates

**Inter-thread Communication**: Qt signals/slots for thread-safe GUI updates and component coordination.

### Key Components

**VoiceAssistant (voice_assistant.py)**
- Central coordinator managing all components
- Handles recording state and workflow orchestration
- Emits Qt signals for GUI updates and status messages

**ApplicationManager (application_manager.py)**  
- Single instance enforcement using socket binding
- Logging configuration and directory management
- Permission checking and comprehensive environment reporting
- Startup behavior management with configurable window visibility

**HotkeyManager (hotkey_manager.py)**
- Global hotkey detection supporting F-keys and modifier combinations
- Configurable hotkey parsing: f9, f10, f11, f12, ctrl+space, alt+space, option+space
- macOS-specific pynput integration with Option key support

**AudioHandler (audio_handler.py)**
- PyAudio-based microphone capture with device selection
- Real-time audio level monitoring with callback system
- Temporary WAV file management and cleanup

**WhisperTranscriber (transcriber.py)**
- faster-whisper model loading with CPU/GPU device optimization
- Multiple model size support: tiny → base → small → medium → large
- Confidence-based filtering and silence detection

**OllamaClient (llm_client.py)**
- HTTP client for local Ollama server integration
- Model management and availability checking
- Configurable prompts for text correction and enhancement

**AutoTyper (auto_typer.py)**
- Cross-platform cursor position typing using pynput
- Application exclusion system to prevent typing in sensitive apps
- Configurable typing speed and delays

**PermissionManager (permission_manager.py)**
- Comprehensive macOS permission checking using multiple detection methods
- Real-time permission status monitoring with visual indicators
- Integration with PyObjC frameworks for native permission APIs

**Config (config.py)**
- JSON-based configuration with runtime updates
- Bundled app support with user home directory fallback
- Default configuration covering all components

### macOS Integration

**Required Permissions:**
- **Microphone Access**: For voice recording (NSMicrophoneUsageDescription)
- **Input Monitoring**: For global hotkeys (NSInputMonitoringUsageDescription)  
- **Accessibility**: For auto-typing functionality (NSAppleEventsUsageDescription)

**Code Signing Requirements:**
- Developer ID Application certificate for proper permission dialogs
- Entitlements file with microphone and input monitoring capabilities
- Runtime hardening for macOS security compliance

**Bundle Configuration:**
- Info.plist with comprehensive usage descriptions
- Bundle identifier: com.chrisventer.speechy
- Icon and metadata configuration for native macOS appearance

## ⚠️ CRITICAL: Hotkey Stability Information

**WORKING BASELINE: Recent commits have confirmed working hotkeys**
- ✅ Global hotkeys (F9) work perfectly with current implementation
- ✅ All functionality confirmed: recording, transcription, auto-typing, LLM processing
- ✅ All macOS permissions properly detected and working

**Known Hotkey Breaking Patterns:**
- ⚠️ Timing measurements during component initialization interfere with pynput
- ❌ Splash screen implementations break hotkeys (QSplashScreen causes Qt event loop interference)
- ⚠️ Changes to application startup sequence must be tested for hotkey compatibility
- ⚠️ GUI components shown before hotkey manager initialization can cause timing conflicts

**Testing Hotkeys After Changes:**
1. Run: `python main.py`
2. Wait for "Hotkey listener started for: f9" log message
3. Press F9 to start recording (should see "Hotkey activated: f9" in logs)
4. Speak test words and press F9 again to stop
5. Verify transcription appears and auto-typing works
6. ❌ If hotkeys fail, immediately revert changes

## Build System Architecture

**PyInstaller Configuration (speechy.spec):**
- Hidden imports for macOS frameworks and PyQt5 components
- Exclusion of heavy ML packages (torch, transformers) for smaller bundle size
- Data files inclusion: icons, plists, entitlements
- Bundle configuration with Info.plist integration

**py2app Alternative (setup.py):**
- Complete app bundle creation with metadata
- Resource inclusion and optimization settings
- Framework-specific includes for macOS compatibility

**Automated Build Script (build_app.sh):**
- Clean build process with artifact removal
- Automatic certificate detection and code signing
- Signature verification and entitlements checking
- Optional DMG creation for distribution

**Build Support Files:**
- `py2app_recipes/` - Custom recipes for faster_whisper and numpy
- `pyinstaller_hooks/` - Custom hooks for problematic dependencies
- `entitlements.plist` - Security entitlements for macOS permissions
- `Info.plist` - App bundle metadata and usage descriptions

## Configuration System

**Config Structure (config.json):**
```json
{
    "hotkey": "f9",
    "whisper_model": "small.en", 
    "ollama_model": "llama3:latest",
    "audio_device_index": null,
    "auto_typing_enabled": false,
    "auto_typing_mode": "raw",
    "auto_typing_excluded_apps": ["Keychain Access", "1Password"],
    "start_minimized": true
}
```

**Startup Behavior:**
- **start_minimized**: Controls whether the application starts with the main window visible or minimized to system tray
- Default: `true` - Application starts minimized with only system tray icon visible
- Set to `false` to show main window on startup
- System tray remains functional regardless of setting
- Users can access the application through system tray icon when minimized

**Model Selection Guidelines:**
- **Whisper**: tiny (fastest) → base (recommended) → small → medium → large (most accurate)
- **Ollama**: llama3.2:1b (fastest) → llama3.2:3b (recommended) → llama3.1:8b (best quality)

**Runtime Configuration:**
- Settings updated through GUI tabs
- Automatic persistence to JSON file
- Live configuration propagation to components

## Development Workflow

**Adding New Features:**
1. Extend appropriate component class (e.g., VoiceAssistant, AudioHandler)
2. Add configuration options to Config.DEFAULT_CONFIG
3. Update GUI tabs in VoiceAssistantGUI for user control
4. Test hotkey functionality after any startup sequence changes
5. Update build configuration if new dependencies are added

**Debugging Common Issues:**
- **Hotkeys not working**: Check Console.app for TCC errors, verify code signing
- **No microphone permission**: Ensure proper code signing with entitlements
- **Whisper model loading fails**: Check disk space and internet for initial download
- **Ollama connection fails**: Verify `ollama serve` is running and models are installed

**Logging System:**
- Development: `voice-assistant/logs/voice_assistant.log`
- Built app: `~/.speechy/logs/voice_assistant.log`
- Structured logging with component-specific prefixes
- Real-time permission status and error reporting

## Platform-Specific Notes

**macOS Requirements:**
- macOS 10.15+ (Catalina) for proper permission system support
- Xcode command line tools for code signing
- Ollama installed and running for LLM functionality
- PyAudio dependency: `brew install portaudio`

**Security Considerations:**
- All speech processing happens locally (no cloud data)
- Proper code signing prevents malicious permission requests
- Application exclusion system prevents typing in sensitive applications
- Temporary audio files are cleaned up after processing