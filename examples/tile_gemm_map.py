#!/bin/env python

import os
import socket

from mpi4py.util.pool import Pool
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Polly


def app_from_kwargs(kwargs):
    kwargs["translator"] = Polly()
    return Polybench(**kwargs)


def remote_measure(kwargs, trs):
    print(f"{trs=}")
    hostname = socket.gethostname()
    print(f"{hostname=}")
    app = app_from_kwargs(kwargs)
    app.transform_list(trs)
    tapp = app.generate_code(alt_infix=f"_tiled_on_{hostname}", ephemeral=False)
    tapp.compile()
    rv = tapp.measure()
    print(f"{rv=}")
    return rv, hostname


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

    with Pool() as pool:
        tile_sizes = [19, 20, 21]
        trs = [[
            [1, 2, TrEnum.FULL_SPLIT],
            [1, 7, TrEnum.TILE_3D, ts, ts, ts],
        ] for ts in tile_sizes]
        print(f"{[kwargs] * len(trs)=}")
        print(f"{trs=}")
        futures = pool.map(remote_measure, [kwargs] * len(trs), trs)

    app = app_from_kwargs(kwargs)
    app.compile()
    print(f"==== original: {app.measure()=}")
    for f in as_completed(futures):
        print(f"**** {f.result()=}")

    print("[END]")


if __name__ == "__main__":
    main()
