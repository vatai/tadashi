#!/usr/bin/env python

from Cython.Build import cythonize
from setuptools import setup

setup(ext_modules=cythonize("tadashi/tadashi.pyx"))
