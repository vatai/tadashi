from tadashi import TrEnum
from tadashi.apps import Simple

app = Simple("./examples/inputs/simple/stencil.c")
app.compile()
print(app.scops[0].schedule_tree[0].yaml_str)

print(f"{app.measure()=}")

app.scops[0].transform_list([[1, TrEnum.TILE1D, 128]])
tile1 = app.generate_code("tile1.c")

tile2 = tile1.generate_code("tile2.c")
tile2.scops[0].transform_list([[3, TrEnum.TILE1D, 16]])

tile2.scops[0].transform_list([[2, TrEnum.INTERCHANGE]])
final_app = tile2.generate_code("final.c")
final_app.compile()
print(f"{final_app.measure()=}")
print("all done")
