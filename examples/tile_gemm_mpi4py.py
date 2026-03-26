#!/bin/env python

import os
import socket

from mpi4py.futures import MPIPoolExecutor, as_completed
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly


def app_from_kwargs(kwargs):
    kwargs["translator"] = Polly()
    return Polybench(**kwargs)


def remote_measure(kwargs, tile_size):
    trs = [
        [1, 2, TrEnum.FULL_SPLIT],
        [1, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
    ]
    print(f"{trs=}")
    hostname = socket.gethostname()
    print(f"{hostname=}")
    app = app_from_kwargs(kwargs)
    app.transform_list(trs)
    tapp = app.generate_code(alt_infix=f"_tiled{tile_size}{hostname}", ephemeral=False)
    tapp.compile()
    rv = tapp.measure()
    return rv


def main():
    print("[BEGIN]")
    kwargs = {
        "benchmark": "gemm",
        "base": "examples/polybench",
        "compiler_options": [
            "-fopenmp",
            "-DEXTRALARGE_DATASET",
        ],
    }

    futures = []
    with MPIPoolExecutor() as executor:
        for tile_size in [19, 20, 21]:
            trs = [
                [1, 2, TrEnum.FULL_SPLIT],
                [1, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
            ]
            future = executor.submit(remote_measure, kwargs, tile_size)
            futures.append(future)

    app = app_from_kwargs(kwargs)
    app.compile()
    print(f"==== original: {app.measure()=}")
    for f in as_completed(futures):
        print(f"**** {f.result()=}")

    print("[END]")


if __name__ == "__main__":
    main()
