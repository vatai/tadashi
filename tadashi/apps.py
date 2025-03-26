#!/usr/bin/env python
import re
import datetime
from colorama import Fore, Style
import os
import shutil
import subprocess
import tempfile
from collections import namedtuple
from pathlib import Path
from typing import Optional, Tuple

from . import Scops

Result = namedtuple("Result", ["legal", "walltime"])


class App:
    scops: Scops
    source: Path
    compiler_options: list[str]
    ephemeral: bool = False

    def __getstate__(self):
        state = {}
        for k, v in self.__dict__.items():
            state[k] = None if k == "scops" else v
        return state

    def _finalize_object(
        self,
        source: str | Path,
        include_paths: Optional[list[str | Path]] = None,
        compiler_options: Optional[list[str]] = None,
    ):
        if include_paths is None:
            include_paths = []
        if compiler_options is None:
            compiler_options = []
        self.compiler_options = compiler_options
        self.compiler_options += [f"-I{p}" for p in include_paths]
        os.environ["C_INCLUDE_PATH"] = ":".join([str(p) for p in include_paths])
        self.source = Path(source)
        self.scops = Scops(str(self.source))

    @classmethod
    def make_ephemeral(cls, *args, **kwargs):
        app = cls(*args, **kwargs)
        app.ephemeral = True
        return app

    def __del__(self):
        if self.ephemeral:
            self.remove_binary()
            self.remove_source()

    def remove_binary(self):
        binary = self.output_binary
        if binary.exists():
            binary.unlink()

    def remove_source(self):
        self.source.unlink()

    @property
    def compile_cmd(self) -> list[str]:
        """Command executed for compilation (list of strings)."""
        raise NotImplementedError()

    def generate_code(self):
        """Create a transformed copy of the app object."""
        raise NotImplementedError()

    @staticmethod
    def extract_runtime(stdout) -> float:
        """Extract the measured runtime from the output."""
        raise NotImplementedError()

    @property
    def output_binary(self) -> Path:
        """The output binary obtained after compilation."""
        # TODO: delete before merge when we fix exit issues
        # print("------------")
        # print(type(self.source), self.source)
        # print(self.source.with_suffix(""))
        # print("------------")
        return self.source.with_suffix("")

    @property
    def run_cmd(self) -> list[Path]:
        """The command which gets executed when we measure runtime."""
        return [self.output_binary]

    def compile(self):
        """Compile the app so it can be measured/executed."""
        result = subprocess.run(self.compile_cmd + self.compiler_options)
        # raise an exception if it didn't compile
        result.check_returncode()

    def measure(self, *args, **kwargs) -> float:
        """Measure the runtime of the app."""
        result = subprocess.run(self.run_cmd, stdout=subprocess.PIPE, *args, **kwargs)
        stdout = result.stdout.decode()
        return self.extract_runtime(stdout)

    def compile_and_measure(self, *args, **kwargs) -> float | str:
        try:
            self.compile()
        except subprocess.CalledProcessError as err:
            return str(err)
        return self.measure(*args, **kwargs)

    def transform_list(
        self, transformation_list: list, run_each: bool = False
    ) -> Result | list[Result]:
        if transformation_list == []:
            run_each = True
        if run_each:
            results = []
            self.compile()
            walltime = self.measure()
            results.append(Result(True, walltime))
        for si, ni, *tr in transformation_list:
            node = self.scops[si].schedule_tree[ni]
            legal = node.transform(*tr)
            if run_each:
                self.compile()
                walltime = self.measure()
                results.append(Result(legal, walltime))
        if not run_each:
            self.compile()
            walltime = self.measure()
            return Result(legal, walltime)
        return results


class Simple(App):
    def __init__(
        self, source: str | Path, compiler_options: Optional[list[str]] = None
    ):
        if compiler_options:
            compiler_options = []
        self._finalize_object(source, compiler_options=compiler_options)

    @property
    def compile_cmd(self) -> list[str]:
        return [
            "gcc",
            str(self.source),
            "-fopenmp",
            "-o",
            str(self.output_binary),
        ]

    @staticmethod
    def extract_runtime(stdout):
        num = stdout.split()[1]
        return float(num)

    def generate_code(self, alt_source=None, ephemeral: bool = True):
        if alt_source:
            new_file = Path(alt_source)
        else:
            mark = "TMPFILE"
            now = datetime.datetime.now()
            now_str = datetime.datetime.isoformat(now)
            suffix = self.source.suffix
            pattern = rf"(.*)(-{mark}\d+-\d+-\d+T\d+:\d+:\d+.\d+.*)({suffix})"
            m = re.match(pattern, str(self.source))
            filename = m.groups()[0] if m else self.source.with_suffix("")
            prefix = f"{filename}-{mark}{now_str}"
            new_file = Path(tempfile.mktemp(prefix=prefix, suffix=suffix, dir="."))
        self.scops.generate_code(self.source, Path(new_file))
        return Simple.make_ephemeral(new_file) if ephemeral else Simple(new_file)


class Polybench(App):
    """A single benchmark in of the Polybench suite."""

    benchmark: Path  # path to the benchmark dir from base
    base: Path  # the dir where polybench was unpacked

    def __init__(
        self,
        benchmark: str,
        base: str,
        infix: str = "",
        compiler_options: Optional[list[str]] = None,
    ):
        if compiler_options is None:
            compiler_options = []
        self.benchmark = Path(benchmark)
        self.base = Path(base)
        path = self.base / self.benchmark
        source = path / Path(self.benchmark.name).with_suffix(".c")
        compiler_options += [
            "-DPOLYBENCH_TIME",
            "-DPOLYBENCH_USE_RESTRICT",
            "-lm",
        ]
        # "-DMEDIUM_DATASET",
        self.utilities = base / Path("utilities")
        self._finalize_object(
            source=self._source_with_infix(source, infix),
            compiler_options=compiler_options,
            include_paths=[self.utilities],
        )

    @staticmethod
    def get_benchmarks(path):
        benchmarks = []
        for file in Path(path).glob("**/*.c"):
            filename = file.with_suffix("").name
            dirname = file.parent.name
            if filename == dirname:
                benchmarks.append(file.parent.relative_to(path))
        return benchmarks

    @property
    def compile_cmd(self) -> list[str]:
        return [
            "gcc",
            str(self.source),
            str(self.utilities / "polybench.c"),
            "-fopenmp",
            "-o",
            str(self.output_binary),
        ]

    def generate_code(self, alt_infix="", ephemeral: bool = True):
        if not alt_infix:
            now = datetime.datetime.now()
            now_str = datetime.datetime.isoformat(now)
            alt_infix = f".{now_str}"
        new_file = self._source_with_infix(self.source, alt_infix)
        self.scops.generate_code(self.source, new_file)
        kwargs = {
            "benchmark": self.benchmark,
            "base": self.base,
            "infix": alt_infix,
            "compiler_options": self.compiler_options,
        }
        return Polybench.make_ephemeral(**kwargs) if ephemeral else Polybench(**kwargs)

    @staticmethod
    def _source_with_infix(source: Path, infix: str):
        return f"{source.with_suffix('')}{infix}{source.suffix}"

    @staticmethod
    def extract_runtime(stdout) -> float:
        result = 0.0
        try:
            result = float(stdout.split()[0])
        except IndexError as e:
            print(f"App probaly crashed: {e}")
        return result
