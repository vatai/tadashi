#!/bin/env python
from pathlib import Path
from random import choice, seed

import tadashi
from tadashi.apps import Simple

seed(1234)

dir_path = Path(__file__).parent
examples_path = dir_path if dir_path.name == "examples" else "examples"
app = Simple(f"{examples_path}/inputs/depnodep.c")
print(app)

node = app.scops[0].schedule_tree[1]
print(f"{node=}")
tr = choice(node.available_transformations)
print(f"{tr=}")
# output:

args = choice(node.get_args(tr, -10, 10))
print(f"{args=}")
# output:

legal = node.transform(tr, *args)
print(f"{legal=}")
# output:

app.compile()
print(f"{app.measure()=}")
transformed_app = app.generate_code()
transformed_app.compile()
print(f"{transformed_app.measure()=}")
# output:
