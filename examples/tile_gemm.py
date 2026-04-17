import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Pet

base = "examples/polybench"

gemm = Polybench(
    "linear-algebra/blas/gemm",
    base=base,
    compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
    translator=Pet(),
)
print(f"{gemm.user_compiler_options=}")

gemm.compile()
otime = gemm.measure(5)
print(f"==== {otime=}")
for tile_size in range(8, 64):
    gemm.reset_scops()
    trs = [
        [0, 2, TrEnum.FULL_SPLIT],
        # [0, 7, TrEnum.TILE_1D, tile_size],
        # [0, 9, TrEnum.TILE_1D, tile_size],
        # [0, 11, TrEnum.TILE_1D, tile_size],
        # [0, 8, TrEnum.INTERCHANGE],
        # [0, 10, TrEnum.INTERCHANGE],
        # [0, 9, TrEnum.INTERCHANGE],
        ###
        [0, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
    ]
    gemm.transform_list(trs)
    # print(gemm.scops[0].schedule_tree[7].yaml_str)
    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}", ephemeral=False)

    tiled.compile()
    ttime = tiled.measure()
    speedup = otime / ttime
    print(f"==== {tile_size=} : {otime=} : {ttime=} : {speedup=}")

print("DONE")
