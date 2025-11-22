#!/usr/bin/env python

import os

from Cython.Build import cythonize
from setuptools import Extension, setup

PROJ_ROOT = os.path.abspath(f"{__file__}/..")
PREFIX = os.path.join(PROJ_ROOT, "third_party/opt")

kwargs = {
    "libraries": ["pet", "isl"],
    "include_dirs": [os.path.join(PREFIX, "include")],
    "library_dirs": [os.path.join(PREFIX, "lib")],
    "runtime_library_dirs": [os.path.join(PREFIX, "lib")],
    "language": "c++",
}

ext_modules = [
    Extension("tadashi", sources=["tadashi/__init__.py"], **kwargs),
    Extension(
        "tadashi.translators",
        sources=["tadashi/translators.py", "tadashi/scop.cc"],
        **kwargs,
    ),
]

setup(ext_modules=cythonize(ext_modules))
