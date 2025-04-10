from pathlib import Path

import tadashi
from tadashi.apps import Simple

path = Path(__file__).parent / "SNAP/ports/snap-c/dim1_sweep.pp.c"
print(path.exists())

app = Simple(path)
print(app.scops[0].schedule_tree[0].yaml_str)
print(f"{__file__} DONE")
