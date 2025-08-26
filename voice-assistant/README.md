# Speechy - Your AI Voice Assistant

A comprehensive Python application that provides voice-to-text transcription using OpenAI Whisper and AI responses through Ollama. The application features hotkey activation, real-time audio recording, local speech transcription, intelligent grammar correction, and automatic typing at your cursor position.

## Features

### Core Functionality
- **Hotkey Activation**: Configurable global hotkey (default F9) for hands-free operation
- **Real-time Audio Recording**: Low-latency microphone capture with visual audio level feedback
- **Local Speech-to-Text**: Uses OpenAI Whisper models running locally for complete privacy
- **AI Grammar Correction**: Connects to Ollama for intelligent grammar correction and filler word removal
- **Auto-Typing**: Types transcriptions directly at cursor position with configurable modes and delays

### Interface & User Experience
- **Professional GUI**: Modern PyQt5 interface with dark theme support
- **System Tray Integration**: Minimalist system tray with right-click menu access
- **Visual Recording Indicator**: Animated recording status with audio level meter
- **Custom About Dialog**: Professional about dialog with clickable links and developer info
- **Tabbed Settings**: Comprehensive settings panel with real-time configuration

### Advanced Features
- **Multiple Auto-Type Modes**: Choose between raw transcription, corrected text, or both
- **Application Exclusions**: Prevent auto-typing in specified applications
- **Configurable Delays**: Customizable typing speed and delay before typing
- **Audio Level Monitoring**: Real-time visual feedback during recording
- **Transcription Logging**: Optional logging of all transcriptions to file
- **Clipboard Integration**: Auto-copy transcriptions to clipboard
- **System Notifications**: Desktop notifications for transcription completion
- **Cross-platform Support**: Works on Windows, macOS, and Linux

## Project Structure

```
voice-assistant/
├── main.py              # Main application entry point and coordination
├── audio_handler.py     # Audio recording and processing with level monitoring
├── transcriber.py       # Whisper speech-to-text integration
├── llm_client.py        # Ollama API client with error handling
├── gui.py              # PyQt5 GUI, system tray, and custom about dialog
├── config.py           # Configuration management with validation
├── auto_typer.py       # Auto-typing functionality with app exclusions
├── requirements.txt    # Python dependencies
├── config.json         # User configuration file (auto-generated)
├── icon.icns           # Application icon for macOS
├── icon.png            # Application icon for other platforms
├── instagram-icon.png  # Instagram icon for about dialog
├── logs/               # Log files directory
├── dist/               # Built application (after PyInstaller)
├── CLAUDE.md          # Development guidance for Claude Code
└── README.md          # This file
```

## Prerequisites

### System Requirements

- Python 3.11 or higher
- Conda (Miniconda or Anaconda)
- Microphone access
- At least 4GB RAM (for Whisper models)
- Internet connection (for initial model downloads)

### Required Software

1. **Ollama**: Download and install from [https://ollama.ai](https://ollama.ai)
2. **PyAudio dependencies** (platform-specific):
   - **macOS**: `brew install portaudio`
   - **Ubuntu/Debian**: `sudo apt-get install portaudio19-dev`
   - **Windows**: Usually works with pip install

## Installation

### 1. Create Conda Environment

```bash
# Clone or download the project
cd voice-assistant

# Create conda environment
conda create -n speechy python=3.11 -y

# Activate environment
conda activate speechy
```

### 2. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# macOS additional step (if needed)
brew install portaudio

# Linux additional step (if needed)
sudo apt-get install portaudio19-dev python3-pyaudio
```

### 3. Set Up Ollama

```bash
# Install Ollama (follow instructions at https://ollama.ai)

# Pull a model (recommended: llama3.2:3b for good performance/quality balance)
ollama pull llama3.2:3b

# Alternative smaller model for lower-end systems
ollama pull llama3.2:1b

# Start Ollama server (usually starts automatically)
ollama serve
```

### 4. Verify Installation

```bash
# Test if Ollama is running
curl http://localhost:11434/api/tags

# Test Python imports
python -c "import faster_whisper, pyaudio, PyQt5; print('All imports successful')"
```

## Configuration

The application uses `config.json` for settings. Default configuration is created automatically on first run.

### Key Settings

```json
{
    "hotkey": "f9",                     // Global hotkey for recording
    "whisper_model": "base",            // Whisper model size
    "ollama_model": "llama3.2:3b",      // Ollama model name
    "ollama_host": "localhost",         // Ollama server host
    "ollama_port": 11434,               // Ollama server port
    "audio_sample_rate": 16000,         // Audio sample rate
    "log_transcriptions": true,         // Log transcriptions to file
    "notification_enabled": true,       // System notifications
    "copy_to_clipboard": true,          // Auto-copy to clipboard
    "auto_typing_enabled": false,       // Enable auto-typing feature
    "auto_typing_mode": "corrected",    // Mode: "raw", "corrected", or "both"
    "auto_typing_delay": 1.0,          // Delay before typing (seconds)
    "auto_typing_speed": 0.02,         // Typing speed (seconds between characters)
    "auto_typing_excluded_apps": []     // Apps to exclude from auto-typing
}
```

### Available Whisper Models

- `tiny`: Fastest, least accurate (~39 MB)
- `base`: Good balance of speed/accuracy (~74 MB) **[Recommended]**
- `small`: Better accuracy, slower (~244 MB)
- `medium`: High accuracy (~769 MB)
- `large`: Best accuracy, slowest (~1550 MB)

### Recommended Ollama Models

- `llama3.2:1b`: Fastest, basic responses (~1.3 GB)
- `llama3.2:3b`: Good balance **[Recommended]** (~2.0 GB)
- `llama3.1:8b`: Higher quality responses (~4.7 GB)
- `mistral`: Alternative model (~4.1 GB)
- `codellama`: Better for code-related queries (~3.8 GB)

## How It Works

Speechy follows a comprehensive workflow for voice-to-text processing, AI correction, and automatic typing:

1. **Hotkey Detection**: User presses the configured hotkey once (default: F9) to start recording
2. **Audio Recording**: Microphone captures audio in real-time with visual level feedback until hotkey is pressed again to stop
3. **Audio Processing**: When recording stops, audio is saved as a temporary WAV file with duration validation
4. **Speech-to-Text**: The audio file is processed by OpenAI Whisper (running locally) to convert speech to text
5. **AI Processing**: The transcribed text is sent to Ollama (local LLM server) to:
   - Correct transcription errors and grammar
   - Remove filler words (um, uh, you know, etc.)
   - Improve clarity while preserving intent
   - Handle punctuation commands (e.g., "comma", "full stop")
6. **Results Display**: Both the original transcription and corrected text are displayed in the GUI
7. **Auto-Typing** (Optional): Based on settings, the application can automatically type:
   - Raw transcription only
   - Corrected text only  
   - Both texts sequentially
8. **Additional Actions**: Text can be automatically copied to clipboard, logged to file, and notifications shown

### AI Correction Examples:
- "I called started the server" → "I cold started the server"
- "I would like to um, start you know the server" → "I would like to start the server"  
- "Send an email to John comma then call Sarah full stop" → "Send an email to John, then call Sarah."

### Auto-Typing Features:
- Types directly at your current cursor position
- Configurable typing speed and delay
- Application exclusion list (prevents typing in password fields, etc.)
- Works across all applications and text fields
- Can be toggled on/off with a single button

The entire process typically takes 2-5 seconds from speaking to seeing results, with all processing happening locally for complete privacy.

## Usage

### Starting the Application

```bash
# Activate conda environment
conda activate speechy

# Run the application
python main.py
```

### Basic Operation

1. **Press the hotkey once** (default: F9) to start recording
2. **Speak clearly** into your microphone
3. **Press the hotkey again** to stop recording
4. **Wait for transcription and correction** (usually 2-5 seconds)
5. **View original transcription and corrected text** in the GUI

**Accessibility Note**: The single-press toggle design makes the application accessible for users who cannot hold down keys.

### GUI Features

- **Main Tab**: Shows recording status, transcription, and AI response with copy/clear buttons
- **Settings Tab**: Configure hotkeys, models, auto-typing, and all features
- **Dynamic Model Selection**: Automatically detects installed Ollama models with refresh button
- **System Tray**: Right-click for quick access to show/hide/quit/record
- **Recording Indicator**: Animated visual feedback with real-time audio level meter
- **Manual Recording**: Use the "Toggle Recording" button as alternative to hotkey
- **Auto-Type Toggle**: Quick on/off button for auto-typing feature in main interface
- **Professional About Dialog**: Custom dialog with developer info and clickable links

### Hotkey Options

- `f5`, `f6`, `f9`, `f10`, `f11`, `f12`: Function keys
- `ctrl+space`: Control + Space
- `alt+space`: Alt + Space

## Troubleshooting

### Common Issues

#### 1. PyAudio Installation Fails

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

**Windows:**
```bash
# Try different PyAudio wheel
pip install pipwin
pipwin install pyaudio
```

#### 2. Whisper Model Download Fails

```bash
# Manually download models
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

#### 3. Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Check available models
ollama list
```

#### 4. Audio Device Issues

```bash
# List audio devices
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]}')
"
```

Then update `config.json`:
```json
{
    "audio_device_index": 1  // Use the device index from above
}
```

#### 5. Hotkey Not Working

- **macOS**: Grant accessibility permissions in System Preferences > Security & Privacy > Accessibility
- **Linux**: May need to run with sudo or configure user permissions
- **Windows**: Run as administrator if needed

#### 6. GUI Not Showing

```bash
# Check if running in virtual environment
echo $CONDA_DEFAULT_ENV

# Try with display variable (Linux)
export DISPLAY=:0
python main.py
```

### Performance Optimization

#### For Lower-End Systems

1. Use smaller models:
   ```json
   {
       "whisper_model": "tiny",
       "ollama_model": "llama3.2:1b"
   }
   ```

2. Reduce audio quality:
   ```json
   {
       "audio_sample_rate": 8000,
       "audio_chunk_size": 512
   }
   ```

#### For Better Quality

1. Use larger models:
   ```json
   {
       "whisper_model": "small",
       "ollama_model": "llama3.1:8b"
   }
   ```

2. Increase audio quality:
   ```json
   {
       "audio_sample_rate": 22050,
       "audio_chunk_size": 2048
   }
   ```

## Development

### Project Architecture

- **`main.py`**: Application entry point and coordination
- **`audio_handler.py`**: Real-time audio capture and processing
- **`transcriber.py`**: Whisper model integration with optimizations
- **`llm_client.py`**: Ollama API client with error handling
- **`gui.py`**: PyQt5 interface with system tray support
- **`config.py`**: Configuration management with validation

### Adding Features

The application is designed to be modular and extensible:

1. **New Hotkeys**: Modify `HotkeyManager` in `main.py`
2. **Different LLM APIs**: Extend `llm_client.py`
3. **Audio Formats**: Enhance `audio_handler.py`
4. **GUI Themes**: Update `gui.py` styling
5. **Cloud Integration**: Add cloud transcription services

### Logging

Logs are written to:
- `logs/voice_assistant.log`: Application logs
- `logs/transcriptions.log`: Transcription history (if enabled)

### Building Executable

For distribution, you can create standalone executables:

```bash
# Install PyInstaller
pip install pyinstaller

# Build using the spec file (recommended)
pyinstaller speechy.spec

# The app will be created at:
# dist/Speechy.app (macOS application bundle)
```

#### Alternative Build Methods

```bash
# Cross-platform generic build (if spec file doesn't work)
pyinstaller --onedir --windowed --icon="icon.icns" --name="Speechy" main.py

# Single file build (not recommended for macOS)
pyinstaller --onefile --windowed --icon="icon.icns" --name="Speechy" main.py
```

#### macOS Application Bundle
The `speechy.spec` build creates a proper `.app` bundle that:
- Can be moved to Applications folder
- Has the correct icon and name in Finder and Launchpad
- Integrates properly with macOS (appears in Spotlight, etc.)
- Includes all dependencies in a single distributable file
- Works without Python installed on the target machine
- Follows macOS application conventions and structure

#### Build Files Explanation
- **`speechy.spec`**: PyInstaller specification file with optimized settings for macOS
- **`dist/Speechy.app`**: Final application bundle ready for distribution
- **`build/`**: Temporary build files (can be deleted after building)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

For support and questions:
1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Open an issue on the project repository
4. Ensure Ollama and Whisper models are properly installed

## Developer

**Designed and built by Chris Venter**  
🔗 [Instagram: @myaccessibility](https://www.instagram.com/myaccessibility/)

---

**Enjoy Speechy - Your AI Voice Assistant! 🎤🤖**