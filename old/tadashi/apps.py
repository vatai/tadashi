#!/usr/bin/env python
import datetime
import os
import re
import subprocess
import tempfile
from collections import namedtuple
from pathlib import Path
from typing import Optional

from . import LLVMScops, Scops

Result = namedtuple("Result", ["legal", "walltime"])


class App:
    scops: Scops | None
    source: Path
    user_compiler_options: list[str]
    ephemeral: bool = False
    populate_scops: bool = True

    @staticmethod
    def _get_defines(options: list[str]):
        defines = []
        for i, opt in enumerate(options):
            if not opt.startswith("-D"):
                continue
            if opt == "-D":
                if i + 1 >= len(options):
                    raise ValueError("Empty -D comiler option")
                defines.append(options[i + 1])
            else:
                defines.append(opt[2:])
        return defines

    def _finalize_object(
        self,
        source: str | Path,
        include_paths: Optional[list[str]] = None,
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
        if not self.source.exists():
            raise ValueError(f"{self.source=} does not exist!")
        defines = self._get_defines(compiler_options)
        self.scops = Scops(str(self.source), defines) if self.populate_scops else None

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
            if not self.scops.legal:
                raise ValueError("The App is not in a legal state")
        if alt_infix:
            new_file = self._source_with_infix(alt_infix)
        else:
            new_file = self._make_new_filename()
        self.scops.generate_code(self.source, new_file)
        kwargs = {
            "source": new_file,
            "compiler_options": self.user_compiler_options,
            "populate_scops": populate_scops,
        }
        kwargs.update(self._codegen_init_args())
        app = self.__class__(**kwargs)
        app.ephemeral = ephemeral
        return app

    def extract_runtime(self, stdout: str) -> float:
        """Extract the measured runtime from the output."""
        raise NotImplementedError()

    @property
    def output_binary(self) -> Path:
        """The output binary obtained after compilation."""
        return self.source.with_suffix("")

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

    @property
    def legal(self) -> bool:
        return all(s.legal for s in self.scops)


POLYBENCH_BASE = str(Path(__file__).parent.parent / "examples/polybench")


class Polybench(App):
    """A single benchmark in of the Polybench suite."""

    benchmark: str  # path to the benchmark dir from base
    base: Path  # the dir where polybench was unpacked

    def __init__(
        self,
        benchmark: str,
        base: Path = Path(POLYBENCH_BASE),
        compiler_options: Optional[list[str]] = None,
        source: Optional[Path] = None,
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


class SimpleLLVM(App):
    compiler: str

    def __init__(
        self,
        source: Path,
        compiler: str = "clang",
        compiler_options: Optional[list[str]] = None,
        runtime_prefix: str = "WALLTIME: ",
        populate_scops: bool = True,
    ):
        if compiler_options:
            compiler_options = []
        self.runtime_prefix = runtime_prefix
        self.populate_scops = populate_scops
        self._finalize_object_llvm(
            source,
            compiler=compiler,
            compiler_options=compiler_options,
        )

    def _finalize_object_llvm(
        self,
        source: Path,
        compiler: str,
        include_paths: Optional[list[str | Path]] = None,
        compiler_options: Optional[list[str]] = None,
    ):
        if include_paths is None:
            include_paths = []
        if compiler_options is None:
            compiler_options = []
        self.compiler = compiler
        self.user_compiler_options = compiler_options
        os.environ["C_INCLUDE_PATH"] = ":".join(map(str, include_paths))
        self.source = Path(source)
        self.scops = None
        if self.populate_scops:
            self.scops = LLVMScops(self.source, compiler=compiler)
