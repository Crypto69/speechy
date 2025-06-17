# Speechy - Your AI Voice Assistant

A powerful macOS voice assistant that combines OpenAI Whisper for speech-to-text transcription with local Ollama LLMs for intelligent text processing and auto-typing capabilities.

![macOS](https://img.shields.io/badge/macOS-10.15+-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- 🎤 **Real-time Speech-to-Text** - Local Whisper model processing for privacy
- 🤖 **AI Text Enhancement** - Integration with local Ollama LLMs for text correction and improvement
- ⌨️ **Auto-typing** - Automatically type transcribed/corrected text at cursor position
- 🔥 **Global Hotkeys** - F9 to start/stop recording, customizable hotkey support
- 🎛️ **System Tray Integration** - Runs quietly in background with visual recording indicators
- 📊 **Audio Level Monitoring** - Real-time microphone level visualization
- 🔐 **Permission Management** - Comprehensive macOS permission handling with visual status
- 🌙 **Dark Theme UI** - Modern PyQt5 interface with tabbed settings
- 📈 **Model Selection** - Choose between speed vs accuracy for both Whisper and Ollama models

## Quick Start

### Prerequisites

- macOS 10.15+ (Catalina or later)
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Conda (recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd speechy
   ```

2. **Set up environment:**
   ```bash
   # Create conda environment
   conda create -n speechy python=3.10
   conda activate speechy
   
   # Install dependencies
   pip install -r voice-assistant/requirements.txt
   
   # Install macOS frameworks for permissions
   pip install pyobjc-framework-Cocoa pyobjc-framework-AVFoundation pyobjc-framework-Quartz pyobjc-framework-Foundation pyobjc-framework-ApplicationServices
   ```

3. **Start Ollama:**
   ```bash
   ollama serve
   ```

4. **Run Speechy:**
   ```bash
   cd voice-assistant
   python main.py
   ```

## Building for Distribution

### Automated Build (Recommended)

```bash
# One-command build with code signing
./build_app.sh
```

The script will:
- Build with PyInstaller
- Code sign with your Developer ID certificate
- Verify signatures and entitlements
- Optionally create a DMG for distribution

### Manual Build

```bash
# Install PyInstaller
pip install pyinstaller

# Build the app
pyinstaller speechy.spec

# Code sign (required for permissions)
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Christian Venter (4R94388LH8)" \
    --options runtime \
    --entitlements voice-assistant/entitlements.plist \
    dist/Speechy.app
```

### Alternative Build (py2app)

```bash
pip install py2app
python setup.py py2app
```

## Permissions Setup

Speechy requires three macOS permissions to function properly:

### 1. Microphone Access
- **Purpose:** Record your voice for transcription
- **When requested:** First time you try to record
- **Required for:** Core functionality

### 2. Input Monitoring  
- **Purpose:** Detect global hotkeys (F9, etc.)
- **When requested:** First app launch
- **Required for:** Hands-free operation

### 3. Accessibility
- **Purpose:** Auto-typing functionality
- **When requested:** When auto-typing is first used
- **Required for:** Automatic text insertion

### Permission Troubleshooting

If permissions aren't working:

```bash
# Reset all permissions for fresh testing
./reset_permissions.sh

# Check your code signing certificates
security find-identity -p codesigning

# Monitor permission requests in real-time
log show --predicate 'subsystem == "com.apple.TCC"' --last 5m
```

## Usage

### Basic Operation

1. **Start Recording:** Press F9 or click the microphone button
2. **Stop Recording:** Press F9 again
3. **View Results:** Transcription appears in the main window
4. **Auto-type:** Enable in settings to automatically type results

### Hotkey Options

- **F9** (default) - Toggle recording
- **F10, F11, F12** - Alternative hotkeys
- **Ctrl+Space, Alt+Space** - Modifier combinations

### Model Configuration

**Whisper Models (Speed → Accuracy):**
- `tiny` - Fastest, basic accuracy
- `base` - Recommended balance
- `small` - Better accuracy
- `medium` - High accuracy
- `large` - Best accuracy, slower

**Ollama Models (Speed → Quality):**
- `llama3.2:1b` - Fastest response
- `llama3.2:3b` - Recommended balance  
- `llama3.1:8b` - Best quality, slower

### Auto-typing Modes

- **Raw** - Type original transcription
- **Corrected** - Type AI-improved text
- **Both** - Type both versions

## Architecture

### Core Components

- **VoiceAssistant** - Main coordinator
- **AudioHandler** - Microphone capture and processing
- **WhisperTranscriber** - Local speech-to-text processing
- **OllamaClient** - AI text enhancement
- **AutoTyper** - Automatic text insertion
- **PermissionManager** - macOS permission handling
- **VoiceAssistantGUI** - PyQt5 user interface

### Threading Model

- Main thread runs GUI event loop
- Separate threads for audio recording, transcription, AI processing, and auto-typing
- Qt signals/slots for thread-safe communication

## Configuration

Settings are stored in `config.json` and can be modified through the GUI:

- Audio device selection
- Model preferences
- Hotkey configuration
- Auto-typing settings
- Application exclusions

## Development

### Running from Source

```bash
# Activate environment
conda activate speechy
cd voice-assistant

# Run with debug logging
python main.py
```

### Testing Dependencies

```bash
# Verify all imports work
python -c "import faster_whisper, pyaudio, PyQt5; print('All imports successful')"

# Check Ollama connection
curl http://localhost:11434/api/tags

# List available audio devices
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
"
```

## Troubleshooting

### Common Issues

**App won't request microphone permission:**
- Ensure app is properly code signed
- Check Console.app for TCC errors
- Verify bundle ID matches entitlements

**Global hotkeys not working:**
- Grant Input Monitoring permission
- Check Accessibility permission
- Restart app after granting permissions

**Auto-typing not working:**
- Grant Accessibility permission
- Check application exclusion list
- Verify cursor is in a text field

**Whisper model loading fails:**
- Check available disk space
- Verify internet connection for first download
- Try a smaller model (e.g., tiny or base)

**Ollama connection fails:**
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`
- Install a model: `ollama pull llama3.2:3b`

### Debug Logging

The app creates detailed logs in:
- **Development:** `voice-assistant/logs/voice_assistant.log`
- **Built app:** `~/.speechy/logs/voice_assistant.log`

Check these logs for detailed error information.

## System Requirements

- **macOS:** 10.15 (Catalina) or later
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 2GB for models and dependencies
- **Network:** Required for initial model downloads

## Privacy & Security

- **Local Processing:** All speech transcription happens locally using Whisper
- **No Cloud Data:** Voice data never leaves your device
- **Open Source:** Full source code available for audit
- **Secure:** Proper code signing and entitlements for macOS security

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Ollama](https://ollama.ai) for local LLM capabilities
- [PyQt5](https://riverbankcomputing.com/software/pyqt/) for the user interface
- [pynput](https://github.com/moses-palmer/pynput) for global hotkey support

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error details
3. Create an issue with relevant log excerpts
4. Monitor Console.app for system-level errors

---

**Made with ❤️ for macOS users who want powerful, private voice assistance.**