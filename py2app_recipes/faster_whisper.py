"""
py2app recipe for faster_whisper
Handles ctranslate2 and onnxruntime dependencies
"""

def check(cmd, mf):
    m = mf.findNode('faster_whisper')
    if m is None:
        return None
    
    return {
        'packages': ['ctranslate2', 'onnxruntime'],
        'includes': [
            'faster_whisper.transcribe',
            'faster_whisper.feature_extractor', 
            'faster_whisper.tokenizer',
            'faster_whisper.utils',
            'ctranslate2',
            'onnxruntime',
        ],
        'excludes': [
            'faster_whisper.audio',  # May have ffmpeg dependencies
        ]
    }