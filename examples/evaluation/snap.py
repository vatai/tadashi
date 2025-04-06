#!/usr/bin/eval python
from tadashi.apps import App


class Snap(App):
    def __init__(self, source, compiler_options=[]):
        self._finalize_object(source, [], compiler_options)

    @property
    def compile_cmd(self) -> list[str]:
        return ["make", "-j", f"DIM1_SWEEP_C={self.source}"]


snap = Snap("examples/inputs/depnodep.c")

print(" ".join(snap.compile_cmd))
