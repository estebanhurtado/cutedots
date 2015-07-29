from distutils.core import setup
import py2exe

packages=[
    'numpy',
    'scipy',
    'h5py',
    'matplotlib',
    'PySide',
    'OpenGL',
    ]
    
includes=[
    'scipy.linalg.cython_blas',
    'scipy.sparse.csgraph._validation',
    'scipy.linalg.cython_lapack',
    'scipy.special._ufuncs',
    'scipy.special._ufuncs_cxx',
    'h5py.defs',
    'h5py.utils'
    ]

setup(
    windows=['cutedots.py'],
    options={'py2exe':{
        'includes': includes,
        'packages': packages,
        }},
    )
