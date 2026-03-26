#!/bin/env python

import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly

base = "examples/polybench"

gemm = Polybench(
    "linear-algebra/blas/gemm",
    base=base,
    compiler_options=[
        "-fopenmp",
        "-DEXTRALARGE_DATASET",
    ],
    translator=Polly(),
)

gemm.compile()
print(f"==== original: {gemm.measure()=}")
s = gemm.scops[1]
for tile_size in [8, 15, 31, 63]:
    gemm.reset_scops()

    trs = [
        [1, 2, TrEnum.FULL_SPLIT],
        [1, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
    ]
    # print(s.schedule_tree[0].yaml_str)
    gemm.transform_list(trs)
    # for i, n in enumerate(s.schedule_tree):
    #     a = n.available_transformations
    #     print(i, end=" ")
    #     if TrEnum.TILE_2D in a:
    #         print("* ", end="")
    #     print(a)

    # print(s.schedule_tree[0].yaml_str)
    tiled = gemm.generate_code(alt_infix=f"_tiled{tile_size}", ephemeral=False)

    tiled.compile()
    print(f"==== {tile_size=} : {tiled.measure()=}")

print("DONE")
