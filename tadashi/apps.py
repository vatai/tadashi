#!/usr/bin/env python
import datetime
import os
import re
import subprocess
import tempfile
from collections import namedtuple
from pathlib import Path
from typing import Optional

from . import Scops

Result = namedtuple("Result", ["legal", "walltime"])


class App:
    scops: Scops
    source: Path
    user_compiler_options: list[str]
    ephemeral: bool = False

    def __del__(self):
        if self.ephemeral:
            binary = self.output_binary
            if binary.exists():
                binary.unlink()
            self.source.unlink()

    def __getstate__(self):
        """This was probably needed for serialisation."""
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
        self.user_compiler_options = compiler_options
        prev_include_path = os.getenv("C_INCLUDE_PATH", "")
        os.environ["C_INCLUDE_PATH"] = ":".join([str(p) for p in include_paths])
        if prev_include_path:
            os.environ["C_INCLUDE_PATH"] += f":{prev_include_path}"
        self.source = Path(source)
        self.scops = Scops(str(self.source))

    def _source_with_infix(self, alt_infix: str):
        mark = "INFIX"
        suffix = self.source.suffix
        pattern = rf"(.*)(-{mark}-.*)({suffix})"
        m = re.match(pattern, str(self.source))
        filename = m.groups()[0] if m else self.source.with_suffix("")
        prefix = f"{filename}-{mark}-{alt_infix}-"
        return Path(tempfile.mktemp(prefix=prefix, suffix=suffix, dir="."))
        suffix = self.source.suffix
        return self.source.with_suffix(f".{alt_infix}{suffix}")

    @classmethod
    def make_ephemeral(cls, *args, **kwargs):
        app = cls(*args, **kwargs)
        app.ephemeral = True
        return app

    def make_new_app(self, ephemeral, **kwargs):
        kwargs["compiler_options"] = self.user_compiler_options
        return self.make_ephemeral(**kwargs) if ephemeral else self.__class__(**kwargs)

    def make_new_filename(self) -> Path:
        mark = "TMPFILE"
        now = datetime.datetime.now()
        now_str = datetime.datetime.isoformat(now).replace(":", "-")
        suffix = self.source.suffix
        pattern = rf"(.*)(-{mark}-\d+-\d+-\d+T\d+-\d+-\d+.\d+-.*)({suffix})"
        m = re.match(pattern, str(self.source))
        filename = m.groups()[0] if m else self.source.with_suffix("")
        prefix = f"{filename}-{mark}-{now_str}-"
        return Path(tempfile.mktemp(prefix=prefix, suffix=suffix, dir="."))

    @staticmethod
    def compiler():
        return os.getenv("CC", "gcc")

    @property
    def compile_cmd(self) -> list[str]:
        """Command executed for compilation (list of strings)."""
        raise NotImplementedError()

    def generate_code(self):
        """Create a transformed copy of the app object."""
        raise NotImplementedError()

    def reset_scops(self):
        for scop in self.scops:
            scop.reset()

    def extract_runtime(self, stdout: str) -> float:
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

    def compile(self, verbose: bool = False):
        """Compile the app so it can be measured/executed."""
        cmd = self.compile_cmd + self.user_compiler_options
        if verbose:
            print(f"{' '.join(cmd)}")
        result = subprocess.run(cmd)
        # raise an exception if it didn't compile
        result.check_returncode()

    def measure(self, repeat=1, *args, **kwargs) -> float:
        """Measure the runtime of the app."""
        results = []
        for _ in range(repeat):
            result = subprocess.run(
                self.run_cmd, stdout=subprocess.PIPE, *args, **kwargs
            )
            stdout = result.stdout.decode()
            results.append(self.extract_runtime(stdout))
        return min(results)

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
    runtime_prefix: str

    def __init__(
        self,
        source: str | Path,
        compiler_options: Optional[list[str]] = None,
        runtime_prefix: str = "WALLTIME: ",
    ):
        if compiler_options is None:
            compiler_options = []
        self.runtime_prefix = runtime_prefix
        self._finalize_object(source, compiler_options=compiler_options)

    @property
    def compile_cmd(self) -> list[str]:
        return [
            self.compiler(),
            str(self.source),
            "-fopenmp",
            "-o",
            str(self.output_binary),
        ]

    def extract_runtime(self, stdout) -> float:
        for line in stdout.split("\n"):
            if line.startswith(self.runtime_prefix):
                num = line.split(self.runtime_prefix)[1]
                return float(num)
        return 0.0

    def generate_code(self, alt_source=None, ephemeral: bool = True):
        if alt_source:
            new_file = Path(alt_source).absolute()
        else:
            new_file = self.make_new_filename()
        self.scops.generate_code(self.source, Path(new_file))
        kwargs = {"source": new_file}
        return self.make_new_app(ephemeral, **kwargs)


class Polybench(App):
    """A single benchmark in of the Polybench suite."""

    benchmark: Path  # path to the benchmark dir from base
    base: Path  # the dir where polybench was unpacked

    def __init__(
        self,
        benchmark: str,
        base: str,
        compiler_options: Optional[list[str]] = None,
        source: Optional[Path] = None,
    ):
        if compiler_options is None:
            compiler_options = []
        self.benchmark = Path(benchmark)
        self.base = Path(base)
        path = self.base / self.benchmark
        if source is None:
            source = path / Path(self.benchmark.name).with_suffix(".c")
        # "-DMEDIUM_DATASET",
        self.utilities = base / Path("utilities")
        self._finalize_object(
            source=source,
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
            self.compiler(),
            str(self.source),
            str(self.utilities / "polybench.c"),
            "-DPOLYBENCH_TIME",
            "-DPOLYBENCH_USE_RESTRICT",
            "-lm",
            "-fopenmp",
            "-o",
            str(self.output_binary),
        ]

    def generate_code(self, alt_infix=None, ephemeral: bool = True):
        if alt_infix:
            new_file = self._source_with_infix(alt_infix)
        else:
            new_file = self.make_new_filename()
        self.scops.generate_code(self.source, new_file)
        kwargs = {
            "source": new_file,
            "benchmark": self.benchmark,
            "base": self.base,
            # "infix": alt_infix,
        }
        return self.make_new_app(ephemeral, **kwargs)

    def extract_runtime(self, stdout) -> float:
        result = 0.0
        try:
            result = float(stdout.split()[0])
        except IndexError as e:
            print(f"App probaly crashed: {e}")
        return result
