#!/usr/bin/env python

# IGNORE THIS FILE FOR NOW

# Source:
# https://stackoverflow.com/questions/42585210/extending-setuptools-extension-to-use-cmake-in-setup-py

import os
import pathlib

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext as build_ext_orig


class CMakeExtension(Extension):

    def __init__(self, name):
        # don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])


class build_ext(build_ext_orig):
    def run(self):
        for ext in self.extensions:
            self.build_cmake(ext)
        super().run()

    def build_cmake(self, ext):
        cwd = pathlib.Path().absolute()

        # these dirs will be created in build_py, so if you don't have
        # any python sources to bundle, the dirs will be missing
        build_temp = pathlib.Path(self.build_temp)
        print(f"{build_temp=}")
        print(f"{cwd=}")
        build_temp.mkdir(parents=True, exist_ok=True)
        extdir = pathlib.Path(self.get_ext_fullpath(ext.name))
        print(f"{extdir=}")
        extdir.mkdir(parents=True, exist_ok=True)

        # example of cmake args
        config = "Debug" if self.debug else "Release"
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={str(extdir.parent.absolute())}",
            f"-DCMAKE_BUILD_TYPE={config}",
        ]

        # example of build args
        build_args = ["--config", config, "--", "-j4"]

        os.chdir(str(build_temp))
        self.spawn(["cmake", str(cwd)] + cmake_args)
        if not self.dry_run:
            self.spawn(["cmake", "--build", "."] + build_args)
        # Troubleshooting: if fail on line above then delete all possible
        # temporary CMake files including "CMakeCache.txt" in top level dir.
        os.chdir(str(cwd))


setup(
    ext_modules=[CMakeExtension(".")],
    cmdclass={
        "build_ext": build_ext,
    },
    py_limited_api=True,
)
