#!/usr/bin/env python
import socket
from mpi4py import futures
from mpi4py.futures import MPIPoolExecutor as Executor

import tadashi
from halo import Halo
from tadashi.apps import App, Simple

def func(idx):
    return f"FUNC({idx}) on {socket.gethostname()}"

@Halo(spinner="dots")
def main():
    app = Simple("examples/depnodep.c")
    tlist = [
        [0, 1, tadashi.TrEnum.FULL_SHIFT_VAR, 13, 1],
    ]
    print(f"MAIN {socket.gethostname()=}")
    fs = []
    with Executor(max_workers=3) as executor:
        for idx in range(3):
            # fs.append(executor.submit(app.transform_list, tlist))
            fs.append(executor.submit(func, idx))
        print(f"{len(fs)=}")
        while fs:
            done = [f for f in fs if f.done()]
            for f in done:
                print(f"{f.result()=}")
                del fs[fs.index(f)]


if __name__ == "__main__":
    main()
