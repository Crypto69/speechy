"""
py2app recipe for numpy with ctypes fixes
Prevents the massive numpy test suite inclusion
"""

def check(cmd, mf):
    m = mf.findNode('numpy')
    if m is None:
        return None
    
    return {
        'packages': ['numpy'],
        'includes': [
            'numpy._core',
            'numpy.lib',
            'numpy.linalg',
            'numpy.random',
            'numpy.fft',
            'numpy.ctypeslib',
        ],
        'excludes': [
            'numpy.tests',
            'numpy.testing',
            'numpy.distutils',
            'numpy.f2py',
            'numpy.doc',
        ]
    }