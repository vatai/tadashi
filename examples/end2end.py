import tadashi
from tadashi.apps import Simple
app = Simple("examples/depnodep.c")
scops = tadashi.Scops(app)

node = scops[0].schedule_tree[1]
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

scops.generate_code()
app.compile()
print(f"{app.measure()=}")
# output:
