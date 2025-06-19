"""
Simple py2app setup script for Speechy
"""

from setuptools import setup

APP = ['voice-assistant/main.py']
DATA_FILES = []

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
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
    },
    'site_packages': True,
    'strip': False,
}

setup(
    name='Speechy',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)