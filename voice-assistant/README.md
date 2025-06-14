# Voice Assistant

A Python application that provides voice-to-text transcription using OpenAI Whisper and AI responses through Ollama. The application features hotkey activation, real-time audio recording, local speech transcription, and intelligent responses from local LLM models.

## Features

- **Hotkey Activation**: Configurable global hotkey (default F9) for hands-free operation
- **Real-time Audio Recording**: Low-latency microphone capture with visual feedback
- **Local Speech-to-Text**: Uses OpenAI Whisper models running locally for privacy
- **AI Integration**: Connects to Ollama for intelligent responses to transcribed speech
- **System Tray Interface**: Minimalist GUI with system tray support
- **Cross-platform**: Works on Windows, Mac, and Linux
- **Configurable Settings**: JSON-based configuration for all settings
- **Audio Level Monitoring**: Visual feedback during recording
- **Transcription Logging**: Optional logging of all transcriptions
- **Clipboard Integration**: Auto-copy transcriptions to clipboard
- **Notifications**: System notifications for transcription completion

## Project Structure

```
voice-assistant/
├── main.py              # Main application entry point
├── audio_handler.py     # Audio recording and processing
├── transcriber.py       # Whisper speech-to-text integration
├── llm_client.py        # Ollama API client
├── gui.py              # PyQt5 GUI and system tray
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── config.json         # User configuration file
├── logs/               # Log files directory
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
    "hotkey": "f9",                    // Global hotkey for recording
    "whisper_model": "base",           // Whisper model size
    "ollama_model": "llama3.2:3b",     // Ollama model name
    "ollama_host": "localhost",        // Ollama server host
    "ollama_port": 11434,              // Ollama server port
    "audio_sample_rate": 16000,        // Audio sample rate
    "log_transcriptions": true,        // Log transcriptions to file
    "notification_enabled": true,      // System notifications
    "copy_to_clipboard": true          // Auto-copy to clipboard
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

The voice assistant follows a simple workflow for voice-to-text processing and AI response correction:

1. **Hotkey Detection**: User presses the configured hotkey once (default: F9) to start recording
2. **Audio Recording**: Microphone captures audio in real-time until hotkey is pressed again to stop
3. **Audio Processing**: When recording stops, audio is saved as a temporary WAV file
4. **Speech-to-Text**: The audio file is processed by OpenAI Whisper (running locally) to convert speech to text
5. **AI Processing**: The transcribed text is sent to Ollama (local LLM server) to correct transcription errors, remove filler words, and clarify intent
6. **Results Display**: Both the original transcription and corrected text are displayed in the GUI
7. **Optional Actions**: Corrected text can be automatically copied to clipboard and logged to file

**Note**: The AI's purpose is transcription correction and clarity, not general conversation. For example:
- "I called started the server" → "I cold started the server"
- "I would like to um, start you know the server" → "I would like to start the server"

The entire process typically takes 2-5 seconds from speaking to seeing the corrected text, with all processing happening locally for privacy.

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

- **Main Tab**: Shows recording status, transcription, and AI response
- **Settings Tab**: Configure hotkeys, models, and features
- **System Tray**: Right-click for quick access to show/hide/quit
- **Recording Indicator**: Visual feedback with audio level meter
- **Manual Recording**: Use the "Start Recording" button as alternative to hotkey

### Hotkey Options

- `f9`, `f10`, `f11`, `f12`: Function keys
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

# Create executable
pyinstaller --onefile --windowed main.py

# The executable will be in dist/
```

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

---

**Enjoy your new voice assistant! 🎤🤖**