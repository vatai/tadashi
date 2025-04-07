import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

base = "examples/polybench"

gemm = Polybench(
    "linear-algebra/blas/gemm",
    base,
    compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
)
print(f"{gemm.user_compiler_options=}")

gemm.compile()
print(f"{gemm.measure()=}")
for tile_size in [64, 100, 128]:
    gemm.reset_scops()
    trs = [
        [0, 2, TrEnum.FULL_SPLIT],
        [0, 3, TrEnum.TILE2D, tile_size],
        [0, 9, TrEnum.TILE3D, tile_size],
    ]
    gemm.transform_list(trs)
    # print(gemm.scops[0].schedule_tree[9].yaml_str)
    tiled = gemm.generate_code(alt_infix="_tiled{tile_size}", ephemeral=False)

    tiled.compile()
    print(f"{tile_size=} : {tiled.measure()=}")

print("DONE")
