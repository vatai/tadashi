#!/usr/bin/env python

import subprocess
from pathlib import Path


class App:
    def compile(self) -> bool:
        raise NotImplementedError()

    @property
    def source_path(self) -> Path:
        raise NotImplementedError()

    @property
    def include_paths(self) -> list[str]:
        raise []

    @property
    def output_binary(self) -> str:
        raise NotImplementedError()

    def measure(self) -> float:
        raise NotImplementedError()


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
    def output_binary(self) -> str:
        return self.source_path.parent / self.benchmark.name

    @property
    def utilities_path(self) -> Path:
        return self.base / "utilities"

    @property
    def include_paths(self) -> list[str]:
        return [str(self.utilities_path)]

    def compile(self):
        cmd = [
            "gcc",
            self.source_path,
            self.utilities_path / "polybench.c",
            "-I",
            self.utilities_path,
            "-o",
            self.output_binary,
            "-DPOLYBENCH_TIME",
        ]
        subprocess.run(cmd)

    def measure(self) -> float:
        cmd = [self.output_binary]
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        return float(result.stdout.decode().split()[0])
