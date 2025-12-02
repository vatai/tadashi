#!/bin/env python

import abc
from pathlib import Path
from typing import Optional

from .translators import Translator


class BaseApp(abc.ABC):

    user_compiler_options: list[str]
    ephemeral: bool = False
    populate_scops: bool = True

    def __init__(self, source: str, translator: Translator):
        self.source = source
        self.translator = translator.set_source(source)

    @property
    def scops(self):
        return self.translator.scops


class Simple(BaseApp):
    runtime_prefix: str

    def __init__(
        self,
        source: str | Path,
        compiler_options: Optional[list[str]] = None,
        runtime_prefix: str = "WALLTIME: ",
        ephemeral: bool = False,
        populate_scops: bool = True,
    ):
        if compiler_options is None:
            compiler_options = []
        self.ephemeral = ephemeral
        self.populate_scops = populate_scops
        self.runtime_prefix = runtime_prefix
        self._finalize_object(source, compiler_options=compiler_options)

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
