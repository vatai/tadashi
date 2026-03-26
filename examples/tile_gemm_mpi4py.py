#!/bin/env python

import os
import socket

from mpi4py.futures import MPIPoolExecutor, as_completed
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly


def app_from_kwargs(kwargs):
    cls = kwargs["translator"]
    kwargs["translator"] = cls()
    return Polybench(**kwargs)


def remote_measure(kwargs, trs):
    print(f"{trs=}")
    hostname = socket.gethostname()
    print(f"{hostname=}")
    app = app_from_kwargs(kwargs)
    tapp = app.generate_code(alt_infix=f"_tiled{tile_size}{hostname}", ephemeral=False)
    tapp.compile()
    rv = tapp.measure(repeat=5)
    return rv


def main():
    kwargs = {
        "benchmark": "gemm",
        "base": "examples/polybench",
        "compiler_options": [
            "-fopenmp",
            "-DEXTRALARGE_DATASET",
        ],
        "translator": Polly,
    }
    app = app_from_kwargs(kwargs)

    futures = []
    with MPIPoolExecutor() as executor:
        for tile_size in [8, 15, 31]:
            trs = [
                [1, 2, TrEnum.FULL_SPLIT],
                [1, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
            ]
            futures.append(executor.submit(remote_measure(kwargs, trs)))

    app.compile()
    print(f"==== original: {app.measure()=}")
    for f in as_completed(futures):
        print(f"**** {f.result(5)=}")

    print("DONE")


if __name__ == "__main__":
    main()
