#!/usr/bin/env python

import subprocess
from pathlib import Path


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

    def measure(self) -> float:
        cmd = [self.output_binary]
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        stdout = result.stdout.decode()
        runtime = self.extract_runtime(stdout)
        return float(runtime)

    @staticmethod
    def extract_runtime(stdout) -> float:
        raise NotImplementedError()


class Simple(App):
    source: Path

    def __init__(self, source: str):
        self.source = Path(source)

    @property
    def compile_cmd(self) -> list[str]:
        return [
            "gcc",
            str(self.source_path),
            "-o",
            str(self.output_binary),
        ]

    @property
    def source_path(self) -> Path:
        return self.source

    @property
    def output_binary(self) -> Path:
        return self.source.with_suffix("")

    @staticmethod
    def extract_runtime(stdout):
        return "42.0"


class Polybench(App):
    """A single benchmark in of the Polybench suite."""

    benchmark: Path  # path to the benchmark dir from base
    base: Path  # the dir where polybench was unpacked

    def __init__(self, benchmark: str, base: str):
        self.benchmark = Path(benchmark)
        self.base = Path(base)

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
    def compile_cmd(self) -> list[str]:
        return [
            "gcc",
            str(self.source_path),
            str(self.utilities_path / "polybench.c"),
            "-I",
            str(self.include_paths[0]),
            "-o",
            str(self.output_binary),
            "-DPOLYBENCH_TIME",
            "-DPOLYBENCH_USE_RESTRICT",
        ]

    @staticmethod
    def extract_runtime(stdout) -> float:
        return float(stdout.split()[0])
