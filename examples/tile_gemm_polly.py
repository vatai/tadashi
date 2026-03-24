import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly

base = "examples/polybench"

gemm = Polybench(
    "linear-algebra/blas/gemm",
    base=base,
    compiler_options=["-DEXTRALARGE_DATASET"],
    translator=Polly(),
)

gemm.compile()
print(f"==== original: {gemm.measure()=}")
for tile_size in [31, 100]:
    gemm.reset_scops()
    trs = [
        # [0, 1, TrEnum.FULL_FUSE],
        # [0, 2, TrEnum.FULL_FUSE],
        [0, 7, TrEnum.TILE_2D, 32, 32],
    ]
    gemm.transform_list(trs)
    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}", ephemeral=False)

    tiled.compile()
    print(f"==== {tile_size=} : {tiled.measure()=}")

print("DONE")
