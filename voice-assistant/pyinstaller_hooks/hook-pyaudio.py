"""PyInstaller hook for PyAudio package."""

from PyInstaller.utils.hooks import collect_dynamic_libs

# Collect dynamic libraries for PyAudio
binaries = collect_dynamic_libs('pyaudio')

# Add hidden imports
hiddenimports = ['pyaudio']