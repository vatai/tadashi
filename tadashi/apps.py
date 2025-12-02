#!/bin/env python

import abc
from pathlib import Path
from typing import Optional

from .scop import Scop
from .translators import Translator


class App(abc.ABC):

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
        source: str,
        translator: Translator,
        compiler_options: Optional[list[str]] = None,
        ephemeral: bool = False,
        populate_scops: bool = True,
    ):
        self.source = source
        self.translator = translator.set_source(source)
        if compiler_options is None:
            compiler_options = []
        self.ephemeral = ephemeral
        self.populate_scops = populate_scops

    @property
    def scops(self) -> list[Scop]:
        """The `Scop` list forwarded from `App.translator` (both for
        compatibility and convenience reasons)."""
        return self.translator.scops

    @property
    @abc.abstractmethod
    def compile_cmd(self):
        pass


class Simple(App):
    runtime_prefix: str

    def __init__(
        self,
        source: str,
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
