#!/bin/env python

import abc
import datetime
import re
import tempfile
from pathlib import Path
from typing import Optional

from .scop import Scop
from .translators import Translator


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
        self.source = source
        if populate_scops:
            self.translator = translator.set_source(source)
        else:
            self.translator = None
        if compiler_options is None:
            compiler_options = []
        self.user_compiler_options = compiler_options
        self.ephemeral = ephemeral
        self.populate_scops = populate_scops

    @property
    def scops(self) -> list[Scop]:
        """The `Scop` list forwarded from `App.translator` (both for
        compatibility and convenience reasons)."""
        return self.translator.scops()

    def generate_code(
        self,
        alt_infix=None,
        ephemeral: bool = True,
        populate_scops: bool = False,
        ensure_legality: bool = True,
    ):
        """Create a transformed copy of the app object."""
        if ensure_legality:
            if not self.scops:
                raise ValueError(
                    "The App was created without scops, cannot check legality"
                )
            if not all(s.legal for s in self.scops):
                raise ValueError("The App is not in a legal state")
        if alt_infix:
            new_file = self._source_with_infix(alt_infix)
        else:
            new_file = self._make_new_filename()
        self.translator.generate_code(str(self.source), str(new_file))
        kwargs = {
            "source": new_file,
            "translator": self.translator,
            "compiler_options": self.user_compiler_options,
            "populate_scops": populate_scops,
        }
        kwargs.update(self.codegen_init_args())
        app = self.__class__(**kwargs)
        app.ephemeral = ephemeral
        return app

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


class Simple(App):
    runtime_prefix: str

    def __init__(
        self,
        source: str | Path,
        translator: Translator,
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
        return [
            self.compiler(),
            str(self.source),
            "-fopenmp",
        ]

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
        translator: Translator = None,
        base: Path = Path(POLYBENCH_BASE),
        compiler_options: Optional[list[str]] = None,
        ephemeral: bool = False,
        populate_scops: bool = True,
    ):
        if compiler_options is None:
            compiler_options = []
        self.ephemeral = ephemeral
        self.populate_scops = populate_scops
        self.base = Path(base)
        self.benchmark = self._get_benchmark(benchmark)
        if source is None:
            filename = Path(self.benchmark).with_suffix(".c").name
            source = self.base / self.benchmark / filename
        # "-DMEDIUM_DATASET",
        self._finalize_object(
            source=source,
            compiler_options=compiler_options,
            include_paths=[self.base / "utilities"],
        )

    def _get_benchmark(self, benchmark: str) -> str:
        target = Path(benchmark).with_suffix(".c").name
        for c_file in self.base.glob("**/*.c"):
            if c_file.with_suffix(".c").name == target:
                if c_file.parent.name == "utilities":
                    break  # go to raise ValueError!
                return str(c_file.relative_to(self.base).parent)
        raise ValueError(f"Not a polybench {benchmark=}")

    def _codegen_init_args(self):
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
        return [
            self.compiler(),
            str(self.source),
            str(self.base / "utilities/polybench.c"),
            "-DPOLYBENCH_TIME",
            "-DPOLYBENCH_USE_RESTRICT",
            "-lm",
            "-fopenmp",
        ]

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
