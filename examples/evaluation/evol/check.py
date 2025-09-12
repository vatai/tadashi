#!/bin/env python
import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench


def compare(kernel, trs, rep=3):
    compiler_options = ["-DEXTRALARGE_DATASET", "-O3"]
    app = Polybench(kernel, compiler_options=compiler_options)
    legal = app.scops[0].transform_list(trs)
    print(f"{legal=}")
    tapp = app.generate_code()

    app.compile()
    tapp.compile()
    baseline = app.measure(rep)
    transformed = tapp.measure(rep)
    print(f"{baseline=} {transformed=}")
    print(f"{baseline/transformed=}")


def main():
    gemm = [
        [1, TrEnum.FULL_SHIFT_PARAM, 2, 16],
        [
            2,
            TrEnum.FULL_FUSE,
        ],
        [1, TrEnum.SET_PARALLEL, 6],
        [2, TrEnum.FULL_SHIFT_PARAM, 1, 48],
        [2, TrEnum.TILE2D, 32, 32],
        [3, TrEnum.SET_LOOP_OPT, 0, 3],
    ]
    compare("gemm", gemm)

    jacobi2d = [
        [9, TrEnum.TILE1D, 32],
        [4, TrEnum.TILE2D, 32, 32],
        [10, TrEnum.TILE2D, 32, 32],
        [10, TrEnum.TILE1D, 32],
        [13, TrEnum.INTERCHANGE],
    ]
    compare("jacobi-2d", jacobi2d)


if __name__ == "__main__":
    main()
    print("DONE")
