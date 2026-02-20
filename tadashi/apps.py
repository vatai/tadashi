#!/bin/env python

import abc
import copy
import datetime
import os
import re
import subprocess
import tempfile
from collections import namedtuple
from pathlib import Path
from typing import Optional

from .scop import Scop
from .translators import Pet, Translator

Result = namedtuple("Result", ["legal", "walltime"])


class App(abc.ABC):
    """The (abstract) base class for app objects."""

    user_compiler_options: list[str]
    """User compiler options are passed to the compilation command."""

    ephemeral: bool = False
    """Ephemeral, i.e. short lived apps.

    If set to `True`, the files of the `App` (usually `App.source`) is
    deleted in the destructor of the Python `App` object.

    """

    populate_scops: bool = True
    """For an `App` that is not intended for transformations.

    If set to `False` populating `App.scops` is skipped. This is
    useful to create a "shallow copy" of an `App`.

    """

    def __del__(self):
        if self.ephemeral:
            binary = self.output_binary
            if binary.exists():
                binary.unlink()
            if self.source.exists():
                self.source.unlink()
            else:
                print("WARNING: source file missing!")

    def __init__(
        self,
        source: str | Path,
        translator: Optional[Translator] = None,
        compiler_options: Optional[list[str]] = None,
        ephemeral: bool = False,
        populate_scops: bool = True,
    ):
        """Construct an app object.

        Args:

          source: The source file.
          translator: See `Translator`.
        """
        self.source = Path(source)
        if translator is None and populate_scops:
            translator = Pet()
        amended_options = self._amend_compiler_options(compiler_options)
        if populate_scops and translator:
            self.translator = translator.set_source(source, amended_options)
        else:
            self.translator = None
        self.user_compiler_options = compiler_options
        self.ephemeral = ephemeral
        self.populate_scops = populate_scops

    def _amend_compiler_options(self, compiler_options: list[str] | None = None):
        if compiler_options is None:
            compiler_options = []
        return compiler_options

    def __getstate__(self):
        """This was probably needed for serialisation."""
        state = {}
        for k, v in self.__dict__.items():
            state[k] = None if k == "translator" else v
        return state

    @property
    def scops(self) -> list[Scop]:
        """The `Scop` list forwarded from `App.translator` (both for
        compatibility and convenience reasons)."""
        if self.translator == None:
            return None
        return self.translator.scops

    @property
    def legal(self) -> bool:
        return self.translator.legal()

    def transform_list(self, transformation_list: list) -> Result:
        for si, ni, *tr in transformation_list:
            node = self.scops[si].schedule_tree[ni]
            legal = node.transform(*tr)
        self.compile()
        walltime = self.measure()
        return Result(legal, walltime)

    def reset_scops(self):
        for scop in self.scops:
            scop.reset()

    @property
    def output_binary(self) -> Path:
        """The output binary obtained after compilation."""
        return self.source.with_suffix("")

    def generate_code(
        self,
        alt_infix=None,
        ephemeral: bool = True,
        populate_scops: bool = False,
        ensure_legality: bool = True,
    ):
        """Create a transformed copy of the app object."""
        if ensure_legality:
            if not self.translator.legal():
                raise ValueError("The App is not in a legal state")
        if alt_infix:
            new_file = self._source_with_infix(alt_infix)
        else:
            new_file = self._make_new_filename()
        options = self._amend_compiler_options(self.user_compiler_options)
        new_file = self.translator.generate_code(str(self.source), new_file, options)
        translator = copy.copy(self.translator) if populate_scops else None
        compiler_options = None
        if self.user_compiler_options:
            compiler_options = self.user_compiler_options[:]
        kwargs = {
            "source": new_file,
            "translator": translator,
            "compiler_options": compiler_options,
            "populate_scops": populate_scops,
        }
        kwargs.update(self.codegen_init_args())
        app = self.__class__(**kwargs)
        app.ephemeral = ephemeral
        return app

    def _source_with_infix(self, alt_infix: str):
        mark = "INFIX"
        suffix = self.source.suffix
        pattern = rf"(.*)(-{mark}-.*)({suffix})"
        m = re.match(pattern, str(self.source))
        filename = m.groups()[0] if m else self.source.with_suffix("")
        prefix = f"{filename}-{mark}-{alt_infix}-"
        return Path(tempfile.mktemp(prefix=prefix, suffix=suffix, dir="."))

    def _make_new_filename(self) -> Path:
        mark = "TMPFILE"
        now = datetime.datetime.now()
        now_str = datetime.datetime.isoformat(now).replace(":", "-")
        suffix = self.source.suffix
        pattern = rf"(.*)(-{mark}-\d+-\d+-\d+T\d+-\d+-\d+.\d+-.*)({suffix})"
        m = re.match(pattern, str(self.source))
        filename = m.groups()[0] if m else self.source.with_suffix("")
        prefix = f"{filename}-{mark}-{now_str}-"
        return Path(tempfile.mktemp(prefix=prefix, suffix=suffix, dir="."))

    @property
    @abc.abstractmethod
    def compile_cmd(self) -> list[str]:
        """Command executed for compilation (list of strings)."""
        pass

    def codegen_init_args(self) -> dict:
        return {}

    @staticmethod
    def compiler():
        return [os.getenv("CC", "gcc")]

    def compile(
        self,
        verbose: bool = False,
        extra_compiler_options: list[str] = [],
        output_binary_suffix="",
    ):
        """Compile the app so it can be measured/executed."""
        cmd = self.compile_cmd
        cmd += ["-o", f"{self.output_binary}{output_binary_suffix}"]
        cmd += self._amend_compiler_options(self.user_compiler_options)
        cmd += extra_compiler_options
        if verbose:
            print(f"{' '.join(cmd)}")
        result = subprocess.run(cmd)
        # raise an exception if it didn't compile
        result.check_returncode()

    def measure(self, repeat=1, *args, **kwargs) -> float:
        """Measure the runtime of the app."""
        if not self.output_binary.exists():
            self.compile()
        results = []
        for _ in range(repeat):
            result = subprocess.run(
                str(self.output_binary), stdout=subprocess.PIPE, *args, **kwargs
            )
            stdout = result.stdout.decode()
            results.append(self.extract_runtime(stdout))
        return min(results)

    def extract_runtime(self, stdout: str) -> float:
        """Extract the measured runtime from the output."""
        raise NotImplementedError()


class Simple(App):
    runtime_prefix: str

    def __init__(
        self,
        source: str | Path,
        translator: Optional[Translator] = None,
        compiler_options: Optional[list[str]] = None,
        ephemeral: bool = False,
        populate_scops: bool = True,
        *,
        runtime_prefix: str = "WALLTIME: ",
    ):
        self.runtime_prefix = runtime_prefix
        super().__init__(
            source,
            translator,
            compiler_options=compiler_options,
            ephemeral=ephemeral,
            populate_scops=populate_scops,
        )

    @property
    def compile_cmd(self) -> list[str]:
        cmd = [
            *self.compiler(),
            str(self.source),
            "-fopenmp",
        ]
        return cmd

    def codegen_init_args(self):
        return {"runtime_prefix": self.runtime_prefix}

    def extract_runtime(self, stdout) -> float:
        for line in stdout.split("\n"):
            if line.startswith(self.runtime_prefix):
                num = line.split(self.runtime_prefix)[1]
                return float(num)
        return 0.0


POLYBENCH_BASE = str(Path(__file__).parent.parent / "examples/polybench")


class Polybench(App):
    """A single benchmark in of the Polybench suite."""

    benchmark: str  # path to the benchmark dir from base
    base: Path  # the dir where polybench was unpacked

    def __init__(
        self,
        benchmark: str,
        source: Optional[Path] = None,
        translator: Optional[Translator] = None,
        base: Path = Path(POLYBENCH_BASE),
        compiler_options: Optional[list[str]] = None,
        ephemeral: bool = False,
        populate_scops: bool = True,
    ):
        self.base = Path(base)
        self.benchmark = self._get_benchmark(benchmark)
        if source is None:
            filename = Path(self.benchmark).with_suffix(".c").name
            source = self.base / self.benchmark / filename
        if compiler_options is None:
            compiler_options = []
        super().__init__(
            source,
            translator,
            compiler_options=compiler_options,
            ephemeral=ephemeral,
            populate_scops=populate_scops,
        )

    def _amend_compiler_options(self, compiler_options: list[str] | None = None):
        compiler_options = super()._amend_compiler_options(compiler_options)
        return compiler_options + [f"-I{self.base / 'utilities'}"]

    def _get_benchmark(self, benchmark: str) -> str:
        target = Path(benchmark).with_suffix(".c").name
        for c_file in self.base.glob("**/*.c"):
            if c_file.with_suffix(".c").name == target:
                if c_file.parent.name == "utilities":
                    break  # go to raise ValueError!
                return str(c_file.relative_to(self.base).parent)
        raise ValueError(f"Not a polybench {benchmark=}")

    def codegen_init_args(self):
        return {
            "benchmark": self.benchmark,
            "base": self.base,
        }

    @staticmethod
    def get_benchmarks(path: str = POLYBENCH_BASE):
        benchmarks = []
        for file in Path(path).glob("**/*.c"):
            filename = file.with_suffix("").name
            dirname = file.parent.name
            if filename == dirname:
                benchmarks.append(file.parent.relative_to(path))
        return list(sorted(benchmarks))

    @property
    def compile_cmd(self) -> list[str]:
        cmd = [
            *self.compiler(),
            str(self.source),
            str(self.base / "utilities/polybench.c"),
            "-DPOLYBENCH_TIME",
            "-DPOLYBENCH_USE_RESTRICT",
            "-lm",
            "-fopenmp",
        ]
        return cmd

    def extract_runtime(self, stdout) -> float:
        result = 0.0
        try:
            result = float(stdout.split()[0])
        except IndexError as e:
            print(f"App probaly crashed: {e}")
        return result

    def dump_arrays(self):
        suffix = ".dump"
        self.compile(
            extra_compiler_options=["-DPOLYBENCH_DUMP_ARRAYS"],
            output_binary_suffix=suffix,
        )
        result = subprocess.run(
            f"{self.output_binary}{suffix}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stderr.decode()

    def dump_scop(self):
        src = self.source.read_text()
        lines = []
        inside_scop = False
        for line in src.split("\n"):
            if "#pragma" in line and "endscop" in line:
                break
            if inside_scop:
                print(f"{line}")
                lines.append(line)
            if "#pragma" in line and "scop" in line:
                inside_scop = True
        return "\n".join(lines)
