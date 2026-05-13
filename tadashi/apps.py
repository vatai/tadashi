#!/bin/env python

import abc
import atexit
import copy
import datetime
import logging
import os
import re
import tempfile
from collections import namedtuple
from pathlib import Path
from subprocess import PIPE, CompletedProcess, run
from typing import Optional

from .scop import Scop
from .translators import Pet, Polly, Translator


class App(abc.ABC):
    """The (abstract) base class for app objects."""

    sources: list[Path]
    """The source files being manipulated by the app object."""

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

    def _cleanup(self):
        if self.ephemeral:
            binary = self.output_binary
            self.logger.debug(f"Deleting {binary=} ({binary.exists()=})")
            if binary.exists():
                binary.unlink()
            for source in self.sources:
                if source.exists():
                    source.unlink()
                else:
                    print(f"WARNING: source file ({str(source)}) missing!")

    @property
    def source(self) -> Path:
        """The primary source file being manipulated by the app object."""
        return self.sources[0]

    @source.setter
    def source(self, value: str | Path) -> None:
        self.sources = [Path(value)]

    @property
    def translator(self) -> Optional[Translator]:
        """The primary source translator."""
        if not self.translators:
            return None
        return self.translators[0]

    @translator.setter
    def translator(self, value: Optional[Translator]) -> None:
        self.translators = [value]

    @property
    def scops(self) -> list[Scop]:
        """The `Scop` list forwarded from `App.translator` (both for
        compatibility and convenience reasons)."""
        if self.translator == None:
            return None
        return self.translator.scops

    @property
    def legal(self) -> bool:
        return all(t.legal() for t in self.translators if t is not None)

    @staticmethod
    def _allowed(item: int | str, allow: list, block: list):
        if allow and block:
            raise ValueError("Can't specify both allow and block lists")
        rv = True
        if allow:
            rv = item in allow
        if block:
            rv = item not in block
        return rv

    def get_all_transformations(
        self,
        *,
        source_allow: Optional[list[int]] = None,
        source_block: Optional[list[int]] = None,
        scop_allow: Optional[list[int]] = None,
        scop_block: Optional[list[int]] = None,
        tr_allow: Optional[list[str]] = None,
        tr_block: Optional[list[str]] = None,
    ) -> list[list[int | str]]:
        """Return all available source/scop/node/transformation tuples."""
        rv = []
        for source_idx, translator in enumerate(self.translators):
            if translator is None:
                continue
            if not self._allowed(source_idx, source_allow, source_block):
                continue
            for si, s in enumerate(translator.scops):
                if self._allowed(si, scop_allow, scop_block):
                    for ni, node in enumerate(s.schedule_tree):
                        # TODO tr_block should be built into available_transformations
                        block = translator.tr_block()
                        av = [t for t in node.available_transformations if t not in block]
                        for tr in av:
                            if self._allowed(tr, tr_allow, tr_block):
                                rv.append((source_idx, si, ni, tr))
        return rv

    def transform_list(self, transformation_list: list) -> None:
        for source_idx, si, ni, *tr in transformation_list:
            translator = self.translators[source_idx]
            node = translator.scops[si].schedule_tree[ni]
            node.transform(*tr)

    def reset_scops(self):
        for translator in self.translators:
            if translator is None:
                continue
            for scop in translator.scops:
                scop.reset()
            translator.reset()

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
            if not self.legal:
                raise ValueError("The App is not in a legal state")
        new_files = [
            self._source_with_infix(source, alt_infix)
            if alt_infix
            else self._make_new_filename(source)
            for source in self.sources
        ]
        options = self.app_required_options() + self.user_compiler_options
        for idx, translator in enumerate(self.translators):
            if translator is None:
                continue
            msg = f"generate_code({str(self.sources[idx])=}, {new_files[idx]=}, {options=})"
            self.logger.debug(msg)
            new_files[idx] = translator.generate_code(
                str(self.sources[idx]), new_files[idx], options
            )
            self.logger.debug(f"Return value: {new_files[idx]=}")
        translators = [copy.copy(t) if t is not None else None for t in self.translators]
        if not populate_scops:
            translators = None
        compiler_options = None
        if self.user_compiler_options:
            compiler_options = self.user_compiler_options[:]
        kwargs = {
            "source": new_files,
            "translator": translators,
            "compiler_options": compiler_options,
            "populate_scops": populate_scops,
        }
        kwargs.update(self.codegen_init_args())
        app = self.__class__(**kwargs)
        app.ephemeral = ephemeral
        return app

    def _source_with_infix(self, source: Path, alt_infix: str):
        mark = "INFIX"
        suffix = source.suffix
        pattern = rf"(.*)(-{mark}-.*)({suffix})"
        m = re.match(pattern, str(source))
        filename = m.groups()[0] if m else source.with_suffix("")
        prefix = f"{filename}-{mark}-{alt_infix}-"
        return Path(tempfile.mktemp(prefix=prefix, suffix=suffix, dir="."))

    def _make_new_filename(self, source: Path) -> Path:
        mark = "TMPFILE"
        now = datetime.datetime.now()
        now_str = datetime.datetime.isoformat(now).replace(":", "-").replace(".", "-")
        suffix = source.suffix
        pattern = rf"(.*)(-{mark}-\d+-\d+-\d+T\d+-\d+-\d+.\d+-.*)({suffix})"
        m = re.match(pattern, str(source))
        filename = m.groups()[0] if m else source.with_suffix("")
        prefix = f"{filename}-{mark}-{now_str}-"
        return Path(tempfile.mktemp(prefix=prefix, suffix=suffix, dir="."))

    def compiler(self) -> list[str]:
        if self.translator:
            return self.translator.get_compiler()
        return [os.getenv("CC", "gcc")]

    def compile(
        self,
        extra_compiler_options: list[str] = [],
        suffix="",
    ):
        """Compile the app so it can be measured/executed."""
        cmd = self.compile_cmd(suffix)
        cmd += extra_compiler_options
        self.logger.debug(f"Running: {' '.join(cmd)}")
        # if log_level is high (e.g. critical) then capture = don't print.
        capture_output = self.logger.getEffectiveLevel() > logging.DEBUG
        proc = run(cmd, capture_output=capture_output)
        if proc.returncode != 0 and capture_output:
            print(f"stdout:\n{proc.stdout.decode()}")
            print(f"stderr:\n{proc.stderr.decode()}")
            print(f"retcode:\n{proc.returncode}")
        if capture_output:
            self.logger.debug(f"{proc.stdout.decode()=}")
            self.logger.debug(f"{proc.stderr.decode()=}")

    def measure(self, repeat=1, *args, **kwargs) -> float:
        """Measure the runtime of the app."""
        if not self.output_binary.exists():
            self.compile()
        results = []
        cmd = self.run_cmd()
        self.logger.debug(f"Running: {' '.join(cmd)} ({repeat=})")
        for _ in range(repeat):
            proc = run(cmd, capture_output=True, *args, **kwargs)
            results.append(self.extract_runtime(proc))
        return min(results)

    def __init__(
        self,
        *,
        source: str | Path | list[str | Path],
        translator: Optional[Translator | list[Optional[Translator]]],
        compiler_options: Optional[list[str]],
        ephemeral: bool,
        populate_scops: bool,
    ):
        """Construct an app object.

        Args:

          source: The source file.

          translator: See `Translator`.

          compiler_options: compiler options used for parsing the
             source file, code generation and compilation.

          populate_scops: [obsolete] `False` should results in
            something similar to invoking this constructor with
            `translator` set to `None`.

        .. todo:: There is much to be done here.

        .. todo:: 1. populate_scops should be obsoleted and then removed.

        .. todo:: 2. order and clarify what should be
            derived/overridden. Maybe even convert App to a proper ABC.

        """
        atexit.register(self._cleanup)
        if isinstance(source, (str, Path)):
            sources = [source]
        else:
            sources = source
        self.sources = [Path(src) for src in sources]
        if not self.sources:
            raise ValueError("At least one source is required")
        if compiler_options is None:
            compiler_options = []
        self.user_compiler_options = compiler_options
        self.ephemeral = ephemeral
        self.populate_scops = populate_scops
        self.translators = self._init_translators(translator, populate_scops)
        if populate_scops:
            options = self.app_required_options() + self.user_compiler_options
            self.translators = [
                tr.set_source(source, options) if tr is not None else None
                for source, tr in zip(self.sources, self.translators)
            ]
        self.logger = logging.getLogger(__name__)

    def _init_translators(
        self,
        translator: Optional[Translator | list[Optional[Translator]]],
        populate_scops: bool,
    ) -> list[Optional[Translator]]:
        if not populate_scops:
            return [None for _ in self.sources]
        if translator is None:
            return [Pet() for _ in self.sources]
        if isinstance(translator, list):
            if len(translator) != len(self.sources):
                raise ValueError("Number of translators must match number of sources")
            return translator
        return [translator if idx == 0 else copy.copy(translator) for idx in range(len(self.sources))]

    @abc.abstractmethod
    def codegen_init_args(self) -> dict:
        return {}

    def app_required_options(self) -> list[str]:
        return []

    @abc.abstractmethod
    def compile_cmd(self, suffix: str) -> list[str]:
        """Command executed for compilation (list of strings)."""
        pass

    @abc.abstractmethod
    def extract_runtime(self, proc: CompletedProcess) -> float:
        """Extract the measured runtime from the output."""
        raise NotImplementedError()

    # @abc.abstractmethod # default behaviour is often acceptable, ergo not abstract
    def run_cmd(self):
        """Construct the command executed in `App.measure`.

        If measuring a benchmark requires running something other then
        `self.output_binary`, potentially with app specific args this
        is the method to override.

        """
        outbin = str(self.output_binary)
        if not self.output_binary.is_absolute():
            outbin = f"./{outbin}"
        return [outbin]


class Simple(App):
    runtime_prefix: str

    def __init__(
        self,
        source: str | Path | list[str | Path],
        translator: Optional[Translator | list[Optional[Translator]]] = None,
        compiler_options: Optional[list[str]] = None,
        ephemeral: bool = False,
        populate_scops: bool = True,
        *,
        runtime_prefix: str = "WALLTIME: ",
    ):
        self.runtime_prefix = runtime_prefix
        super().__init__(
            source=source,
            translator=translator,
            compiler_options=compiler_options,
            ephemeral=ephemeral,
            populate_scops=populate_scops,
        )

    def codegen_init_args(self):
        return {"runtime_prefix": self.runtime_prefix}

    def compile_cmd(self, suffix: str) -> list[str]:
        cmd = [
            *self.compiler(),
            *map(str, self.sources),
            "-fopenmp",
            "-o",
            f"{self.output_binary}{suffix}",
        ]
        return cmd

    def extract_runtime(self, proc: CompletedProcess) -> float:
        stdout = proc.stdout.decode()
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

    def _get_benchmark(self, benchmark: str) -> str:
        target = Path(benchmark).with_suffix(".c").name
        for c_file in self.base.glob("**/*.c"):
            if c_file.with_suffix(".c").name == target:
                if c_file.parent.name == "utilities":
                    break  # go to raise ValueError!
                return str(c_file.relative_to(self.base).parent)
        raise ValueError(f"Not a polybench {benchmark=}")

    @staticmethod
    def get_benchmarks(path: str = POLYBENCH_BASE):
        benchmarks = []
        for file in Path(path).glob("**/*.c"):
            filename = file.with_suffix("").name
            dirname = file.parent.name
            if filename == dirname:
                benchmarks.append(file.parent.relative_to(path))
        return list(map(str, sorted(benchmarks)))

    def dump_arrays(self):
        suffix = ".dump"
        self.compile(
            extra_compiler_options=["-DPOLYBENCH_DUMP_ARRAYS"],
            suffix=suffix,
        )
        result = run(f"{self.output_binary}{suffix}", stdout=PIPE, stderr=PIPE)
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

    def __init__(
        self,
        benchmark: str,
        source: Optional[str | Path | list[str | Path]] = None,
        translator: Optional[Translator | list[Optional[Translator]]] = None,
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
        super().__init__(
            source=source,
            translator=translator,
            compiler_options=compiler_options,
            ephemeral=ephemeral,
            populate_scops=populate_scops,
        )

    def codegen_init_args(self):
        return {
            "benchmark": self.benchmark,
            "base": self.base,
        }

    def app_required_options(self) -> list[str]:
        return [
            f"-I{self.base / 'utilities'}",
            "-DPOLYBENCH_TIME",
            "-DPOLYBENCH_USE_RESTRICT",
        ]

    def compile_cmd(self, suffix) -> list[str]:
        cmd = [
            *self.compiler(),
            *map(str, self.sources),
            str(self.base / "utilities/polybench.c"),
            "-lm",
            "-o",
            f"{self.output_binary}{suffix}",
            *self.app_required_options(),
            *self.user_compiler_options,
        ]
        return cmd

    def extract_runtime(self, proc: CompletedProcess) -> float:
        stdout = proc.stdout.decode()
        result = 0.0
        try:
            result = float(stdout.split()[0])
        except IndexError as e:
            print(f"App probaly crashed: {e}")
        return result
