#!/usr/bin/env python

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class App:

    @property
    def include_paths(self) -> list[Path]:
        return []

    def compile(self) -> bool:
        result = subprocess.run(self.compile_cmd)
        # raise an exception if it didn't compile
        result.check_returncode()
        return result == 0

    @property
    def compile_cmd(self) -> list[str]:
        raise NotImplementedError()

    @property
    def source_path(self) -> Path:
        raise NotImplementedError()

    @property
    def output_binary(self) -> Path:
        raise NotImplementedError()

    @property
    def run_cmd(self) -> list:
        return [self.output_binary]

    def measure(self, *args, **kwargs) -> float:
        result = subprocess.run(self.run_cmd, stdout=subprocess.PIPE, *args, **kwargs)
        stdout = result.stdout.decode()
        return self.extract_runtime(stdout)

    @staticmethod
    def extract_runtime(stdout) -> float:
        raise NotImplementedError()


class Simple(App):
    source: Path
    alt_source: Path
    tmpdir: tempfile.TemporaryDirectory

    def __init__(self, source: str, alt_source: str = ""):
        self.source = Path(source)
        if alt_source:
            self.alt_source = Path(alt_source)
        else:
            self.tmpdir = tempfile.TemporaryDirectory()
            self.alt_source = Path(self.tmpdir.name) / self.source.name
        shutil.copy(self.source, self.alt_source)  # boo

    def __del__(self):
        self.tmpdir.cleanup()

    @property
    def compile_cmd(self) -> list[str]:
        return [
            "gcc",
            str(self.alt_source),
            "-o",
            str(self.output_binary),
        ]

    @property
    def source_path(self) -> Path:
        return self.source

    @property
    def alt_source_path(self) -> Path:
        return self.alt_source

    @property
    def output_binary(self) -> Path:
        return self.alt_source.with_suffix("")

    @staticmethod
    def extract_runtime(stdout):
        num = stdout.split()[1]
        return float(num)


class Polybench(App):
    """A single benchmark in of the Polybench suite."""

    benchmark: Path  # path to the benchmark dir from base
    base: Path  # the dir where polybench was unpacked

    def __init__(self, benchmark: str, base: str, compiler_options=[]):
        self.benchmark = Path(benchmark)
        self.base = Path(base)
        self.compiler_options = compiler_options
        shutil.copy(self.source_path, self.alt_source_path)

    @property
    def source_path(self) -> Path:
        path = self.base / self.benchmark / self.benchmark.name
        return path.with_suffix(".c")

    @property
    def output_binary(self) -> Path:
        return self.source_path.parent / self.benchmark.name

    @property
    def utilities_path(self) -> Path:
        return self.base / "utilities"

    @property
    def include_paths(self) -> list[Path]:
        return [self.utilities_path]

    @property
    def alt_source_path(self) -> Path:
        ext = f".tmp{self.source_path.suffix}"
        return self.source_path.with_suffix(ext)

    @property
    def compile_cmd(self) -> list[str]:
        return [
            "gcc",
            str(self.alt_source_path),
            str(self.utilities_path / "polybench.c"),
            "-I",
            str(self.include_paths[0]),
            "-o",
            str(self.output_binary),
            "-DPOLYBENCH_TIME",
            "-DPOLYBENCH_USE_RESTRICT",
            # "-DMEDIUM_DATASET",
            "-lm",
        ] + self.compiler_options

    @staticmethod
    def extract_runtime(stdout) -> float:
        result = 0
        try:
            result = float(stdout.split()[0])
        except IndexError as e:
            print(f"App probaly crashed: {e}")
        return result
