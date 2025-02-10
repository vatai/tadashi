#!/usr/bin/env python

import time
import socket
import os
import subprocess

print(f"{socket.gethostname()=} (top)")
if not True:
    print("IMPORT CONCURRENT")
    from concurrent import futures
    from concurrent.futures import ThreadPoolExecutor as Executor
else:
    print("IMPORT MPI4PY")
    from mpi4py import futures
    from mpi4py.futures import MPIPoolExecutor as Executor
    # from mpi4py.futures import MPICommExecutor as Executor


def func(task, t):
    print(f"task {task}: sleep for {t}s")
    time.sleep(t)
    print(f"task {task}: sleep for {t}s DONE!")
    return t * task * 10000


def main():
    nodelist = os.environ["SLURM_NODELIST"]
    cmd = ["scontrol", "show", "hostnames", f"{nodelist}"]
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    hosts = result.stdout.read().decode().split('\n')
    host = hosts[1] + '.cloud.r-ccs.riken.jp'
    print(f"{hosts=} and {host=}")
    times = [3, 4, 1, 2, 3, 4, 5] * 100
    info={'host': host}
    with Executor(max_workers=2, info=info) as executor:
        fs = [executor.submit(func, *arg) for arg in enumerate(times[:3])]
        print("-- scheduled --")
        while fs:
            done = [f for f in fs if f.done()]
            for f in done:
                print(f"{f.result()=}")
                del fs[fs.index(f)]


if __name__ == "__main__":
    main()
    print("Done!")
