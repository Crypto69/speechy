"""
py2app setup script for Speechy - Alternative build method to PyInstaller

Usage:
    pip install py2app
    python setup.py py2app
    
The built app will be in dist/Speechy.app
"""

from setuptools import setup

APP = ['voice-assistant/main.py']
DATA_FILES = [
    'icon.icns',
    'voice-assistant/Info.plist',
    'voice-assistant/entitlements.plist'
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
        'NSSupportsAutomaticTermination': True,
        'NSSupportsSuddenTermination': True,
    },
    'packages': [
        'pynput', 
        'pyaudio', 
        'faster_whisper',
        'PyQt5',
        'requests',
        'openai',
        'numpy',
        'torch',
        'objc',
        'Foundation',
        'AppKit',
        'AVFoundation',
        'ApplicationServices',
        'Quartz'
    ],
    'includes': [
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'PyQt5.sip'
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'scipy'
    ],
    'resources': ['icon.icns'],
    'optimize': 1,
}

setup(
    name='Speechy',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    description='Speechy - Your AI Voice Assistant'
)