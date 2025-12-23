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
