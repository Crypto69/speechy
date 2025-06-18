"""PyInstaller hook for faster-whisper package."""

from PyInstaller.utils.hooks import collect_all

# Collect all necessary files for faster-whisper
datas, binaries, hiddenimports = collect_all('faster_whisper')

# Add specific hidden imports that PyInstaller might miss
hiddenimports += [
    'faster_whisper.transcribe',
    'faster_whisper.vad', 
    'faster_whisper.audio',
    'faster_whisper.feature_extractor',
    'faster_whisper.tokenizer',
    'ctranslate2',
    'ctranslate2._ext',
]