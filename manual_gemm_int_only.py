import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench, Simple

base = "examples/polybench"

# gemm = Polybench(
#     "linear-algebra/blas/gemm",
#     base,
#     compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
# )
gemm = Simple("./examples/inputs/simple/gemm.c", compiler_options=["-O3"])
print(f"{gemm.user_compiler_options=}")

gemm.compile()
print(f"{gemm.measure()=}")
gemm.reset_scops()
trs = [
    [0, 2, TrEnum.INTERCHANGE],
]
gemm.transform_list(trs)
#print(gemm.scops[0].schedule_tree[3].yaml_str)
tiled = gemm.generate_code(ephemeral=False)
tiled.compile()
print(f"new time: {tiled.measure()=}")
print(tiled.source)
print("DONE")