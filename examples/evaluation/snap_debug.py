#!/usr/bin/eval python
from pathlib import Path

from tadashi import TrEnum
from tadashi.apps import Simple

app = Simple(Path(__file__).parent / "snap_debug.c")

tapp = app.generate_code()
tapp.compile()
print(tapp.measure())
