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
        return self.benchmark.name

    @property
    def utilities_path(self) -> Path:
        return self.base / "utilities"

    @property
    def include_paths(self) -> list[str]:
        return [str(self.utilities_path)]

    def compile(self):
        compiler_opts_path = self.base / self.benchmark / "compiler.opts"
        compiler_opts = compiler_opts_path.read_text().split()
        cmd = [
            "gcc",
            self.source_path,
            self.utilities_path / "polybench.c",
            "-I",
            self.utilities_path,
            "-o",
            self.output_binary,
            *compiler_opts,
        ]
        compiled_cmd = " ".join(map(str, cmd))
        subprocess.run(cmd)
