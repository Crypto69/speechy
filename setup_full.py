"""
Full standalone py2app setup script for Speechy
Handles complex ML dependencies and avoids PyInstaller conflicts
"""

from setuptools import setup
import py2app
import os

APP = ['voice-assistant/main.py']
DATA_FILES = [
    'icon.icns',
]

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'Speechy',
        'CFBundleDisplayName': 'Speechy',
        'CFBundleIdentifier': 'com.chrisventer.speechy',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': 'Speechy',
        'CFBundleIconFile': 'icon.icns',
        'NSMicrophoneUsageDescription': 'Speechy needs microphone access to record your voice for speech-to-text transcription and AI assistance.',
        'NSAppleEventsUsageDescription': 'Speechy needs to control other applications to enable auto-typing functionality and global hotkey support.',
        'NSInputMonitoringUsageDescription': 'Speechy needs Input Monitoring access to detect global hotkeys (like F9) for hands-free voice recording control.',
        'NSSystemAdministrationUsageDescription': 'Speechy needs system administration access for advanced input monitoring and accessibility features.',
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.productivity',
    },
    # Explicit includes for required modules
    'includes': [
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'PyQt5.sip',
        'faster_whisper',
        'ctranslate2',
        'onnxruntime',
        'numpy',
        'pyaudio',
        'requests',
        'yaml',
        'plyer',
        'pyperclip',
    ],
    # Exclude problematic packages
    'excludes': [
        'tkinter',
        'matplotlib',
        'scipy',
        'test',
        'tests',
        'PyInstaller',  # Exclude PyInstaller to avoid conflicts
        'PyInstaller.hooks',
        'PyInstaller.hooks.hook-PyQt6',
        'PyInstaller.hooks.hook-django',
        'PIL',
        'django',
        'torch',  # Exclude torch unless specifically needed
        'jupyter',
        'notebook',
        'IPython',
        'pandas',
        'sklearn',
    ],
    # Let py2app auto-discover packages to avoid conflicts
    # 'packages': [],
    'resources': ['icon.icns'],
    'optimize': 1,
    'strip': False,  # Don't strip to preserve debugging info
    'prefer_ppc': False,
    'semi_standalone': False,  # Full standalone
    'site_packages': True,
}

setup(
    name='Speechy',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    description='Speechy - Your AI Voice Assistant'
)