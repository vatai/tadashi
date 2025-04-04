from tadashi import TrEnum
from tadashi.apps import Simple

app = Simple("./examples/inputs/simple/gemm.c")
app.compile()
app.measure()
print(app.scops[0].schedule_tree[0].yaml_str)

app.scops[0].transform_list([[1, TrEnum.TILE, 16]])
tile1 = app.generate_code("tile1.c")
tile1.scops[0].transform_list([[3, TrEnum.TILE, 16]])

tile2 = tile1.generate_code("tile2.c")
tile2.scops[0].transform_list([[3, TrEnum.TILE, 16]])

tile2.scops[0].transform_list([[2, TrEnum.INTERCHANGE]])
final_app = tile2.generate_code("final.c")
final_app.compile()
final_app.measure()
print("all done")