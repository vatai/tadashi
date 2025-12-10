#!/usr/bin/env python

import os

from Cython.Build import cythonize
from setuptools import Extension, setup

PROJ_ROOT = os.path.abspath(f"{__file__}/..")
PREFIX = os.path.join(PROJ_ROOT, "third_party/opt")

kwargs = {
    "libraries": ["pet", "isl"],
    "include_dirs": [os.path.join(PREFIX, "include"), "tadashi/src"],
    "library_dirs": [os.path.join(PREFIX, "lib")],
    "runtime_library_dirs": [os.path.join(PREFIX, "lib")],
    "language": "c++",
}

ext_modules = [
    Extension(
        "tadashi.scop",
        ["tadashi/scop.py", "tadashi/src/ccscop.cc", "tadashi/src/transformations.c"],
        **kwargs,
    ),
    Extension(
        "tadashi.translators",
        ["tadashi/translators.py", "tadashi/src/ccscop.cc", "tadashi/src/codegen.c"],
        **kwargs,
    ),
]

setup(ext_modules=cythonize(ext_modules))
