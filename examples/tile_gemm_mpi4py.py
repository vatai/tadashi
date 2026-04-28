#!/bin/env python

import os
import socket

from mpi4py.futures import MPIPoolExecutor, as_completed
from tadashi import TrEnum
from tadashi.apps import Polybench
from tadashi.translators import Pet, Polly


def remote_measure(app, trs, tile_size):
    print(f"{trs=}")
    hostname = socket.gethostname()
    print(f"{hostname=}")
    app.reset_scops()
    app.transform_list(trs)
    tapp = app.generate_code(alt_infix=f"_tiled{tile_size}{hostname}", ephemeral=False)
    tapp.compile()
    rv = tapp.measure()
    return rv, hostname


def main():
    print("[BEGIN]")
    app = Polybench(
        benchmark="gemm",
        base="examples/polybench",
        translator=Polly(),
        compiler_options=["-fopenmp", "-DEXTRALARGE_DATASET"],
    )
    app.compile()
    otime = app.measure()
    print(f"==== original: {otime=}")

    futures = []
    with MPIPoolExecutor() as executor:
        for tile_size in [19, 20, 21]:
            trs = [
                [1, 2, TrEnum.FULL_SPLIT],
                [1, 7, TrEnum.TILE_3D, tile_size, tile_size, tile_size],
            ]
            future = executor.submit(remote_measure, app, trs, tile_size)
            futures.append(future)

    for f in as_completed(futures):
        ttime = f.result()
        print(f"**** {ttime=}")

    print("[END]")


if __name__ == "__main__":
    main()
