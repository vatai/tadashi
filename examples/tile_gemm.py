import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench

base = "examples/polybench"

gemm = Polybench(
    "linear-algebra/blas/gemm",
    base,
    # compiler_options=["-DEXTRALARGE_DATASET"],
)

print(gemm.scops[0].schedule_tree[2].yaml_str)
trs = [
    [0, 7, TrEnum.INTERCHANGE],
    [0, 2, TrEnum.FULL_FUSE],
    [0, 1, TrEnum.TILE, 32],
    [0, 3, TrEnum.TILE, 32],
    [0, 2, TrEnum.INTERCHANGE],
    [0, 2, TrEnum.SET_PARALLEL, 8],
]
gemm.transform_list(trs)
print(gemm.scops[0].schedule_tree[7].yaml_str)
gemm2 = gemm.generate_code(alt_infix=".joao", ephemeral=False)

# print(f"{gemm2.compiler_options=}")
print("DONE")
