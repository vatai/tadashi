#!/usr/bin/env python

import os

from Cython.Build import cythonize
from setuptools import Extension, setup

PROJ_ROOT = os.path.abspath(f"{__file__}/..")
PREFIX = os.path.join(PROJ_ROOT, "third_party/opt")

ext_modules = [
    Extension(
        "tadashi.translators",
        sources=["tadashi/translators.py"],
        libraries=["pet", "isl"],
        include_dirs=[os.path.join(PREFIX, "include")],
        library_dirs=[os.path.join(PREFIX, "lib")],
        runtime_library_dirs=[os.path.join(PREFIX, "lib")],
    )
]

setup(ext_modules=cythonize(ext_modules))
