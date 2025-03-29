import tadashi
from tadashi.apps import Polybench

base = "./examples/polybench"
app = Polybench("stencils/jacobi-2d", base)
print(app.source)

xts = 4
yts = 4
trs = [
    [4, tadashi.TrEnum.TILE, [xts]],
    [6, tadashi.TrEnum.TILE, [yts]],
    [5, tadashi.TrEnum.INTERCHANGE, []],
    # [10, tadashi.TrEnum.TILE, [xts]],
    # [12, tadashi.TrEnum.TILE, [yts]],
    # [11, tadashi.TrEnum.INTERCHANGE, []],
]
print(app.scops[0].schedule_tree[5].yaml_str)

app.scops[0].transform_list(trs)
mod = app.generate_code("foobar.c", ephemeral=False)

print(mod.source)

app.compile()
print(f"{app.measure()=}")
mod.compile()
print(f"{mod.measure()=}")
