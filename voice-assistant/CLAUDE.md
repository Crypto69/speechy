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

**Build Executable:**
```bash
pip install pyinstaller
# For macOS (recommended - creates .app bundle)
pyinstaller --onedir --windowed --icon="icon.icns" --name="Speechy" main.py
# Alternative: single file (not recommended for macOS)
pyinstaller --onefile --windowed --icon="icon.icns" --name="Speechy" main.py
```

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
- Supports F-keys (f9, f10, f11, f12) and modifier combinations (ctrl+space, alt+space)
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
- Requires accessibility permissions for global hotkeys
- PyAudio dependency: `brew install portaudio`

**Linux:**
- May need sudo for global hotkey access
- PyAudio dependency: `sudo apt-get install portaudio19-dev`

**Windows:**
- May need administrator privileges for hotkeys
- PyAudio installation sometimes requires pipwin