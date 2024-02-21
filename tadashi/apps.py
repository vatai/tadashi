#!/usr/bin/env python

import subprocess
from pathlib import Path


class App:
    def compile(self):
        raise NotImplementedError()

    @property
    def source_path(self):
        raise NotImplementedError()

    @property
    def include_paths(self):
        raise NotImplementedError()


class Polybench(App):
    def __init__(self, benchmark: str, base: str):
        self.benchmark = Path(benchmark)
        self.base = Path(base)

    @property
    def source_path(self):
        path = self.base / self.benchmark / self.benchmark.name
        return path.with_suffix(".c")

    @property
    def utilities_path(self):
        return self.base / "utilities"

    @property
    def include_paths(self):
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
            *compiler_opts,
        ]
        compiled_cmd = " ".join(map(str, cmd))
        subprocess.run(cmd)
