#!/usr/bin/env python
import socket

import tadashi
from halo import Halo
from mpi4py import futures
from mpi4py.futures import MPIPoolExecutor as Executor
from tadashi.apps import App, Simple


def func(idx):
    return f"FUNC({idx}) on {socket.gethostname()}"

def compile_and_run(source):
    app = Simple(source)
    app.compile()
    return app.measure()

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
            app.transform_list(tlist)
            new_app = app.generate_code(ephemeral=False)
            print(f"{new_app.source=}")
            fs.append(executor.submit(compile_and_run, str(new_app.source)))
            # fs.append(executor.submit(new_app.compile))
            # fs.append(executor.submit(func, idx))
        print(f"{len(fs)=}")
        while fs:
            done = [f for f in fs if f.done()]
            for f in done:
                print(f"{f.result()=}")
                del fs[fs.index(f)]


if __name__ == "__main__":
    main()
