import tadashi
from tadashi.apps import Polybench

base = "./examples/polybench"
app = Polybench(
    "stencils/jacobi-2d",
    base,
    compiler_options=["-O3"],
)
print(app.source)

xts = 31
yts = 31
trs = [
    [4, tadashi.TrEnum.TILE2D, xts, yts],
]
print(app.scops[0].schedule_tree[5].yaml_str)

app.scops[0].transform_list(trs)
mod = app.generate_code(f"tile{xts}-{yts}", ephemeral=False)

print(mod.source)

app.compile()
print(f"{app.measure()=}")
mod.compile()
print(f"{mod.measure()=}")
