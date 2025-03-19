from pathlib import Path

import tadashi
from tadashi.apps import Simple

app = Simple(f"{Path(__file__).parent}/inputs/depnodep.c")
print(app)
node = app.scops[0].schedule_tree[1]
print(f"{node=}")
tr = tadashi.TrEnum.FULL_SHIFT_VAR
print(f"{tr in node.available_transformations=}")
# output:

print(f"{tr=}")
lu = node.available_args(tr)
print(f"{len(lu)=}")
print(f"{lu[0]=}")
print(f"{lu[1]=}")
# output:

args = [13, 1]
print(f"{node.valid_args(tr, *args)=}")
legal = node.transform(tr, *args)
print(f"{legal=}")
# output:

app.compile()
print(f"{app.measure()=}")
app = app.generate_code()
app.compile()
print(f"{app.measure()=}")
# output:
