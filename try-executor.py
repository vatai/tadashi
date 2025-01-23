#!/usr/bin/env python

import time
from concurrent import futures


def func(task, t):
    print(f"task {task}: sleep for {t}s")
    time.sleep(t)
    print(f"task {task}: sleep for {t}s DONE!")
    return t * task * 10000


def main():
    times = [3, 4, 1, 2, 3, 4, 5]
    with futures.ThreadPoolExecutor(max_workers=4) as executor:
        fs = [executor.submit(func, *arg) for arg in enumerate(times[:])]
        print("-- scheduled --")
        while fs:
            try:
                for f in futures.as_completed(fs, timeout=0):
                    print(f"{f.result()=}")
                    idx = fs.index(f)
                    del fs[idx]
            except TimeoutError as e:
                # print(f"{e=}")
                pass


if __name__ == "__main__":
    main()
    print("Done!")
