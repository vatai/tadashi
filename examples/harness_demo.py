from concurrent import futures

import tadashi
from tadashi.apps import Simple


def func():
    pass


def main():
    app = Simple("examples/depnodep.c")
    node = app.scops[0].schedule_tree[1]
    tr = tadashi.TrEnum.FULL_SHIFT_VAR
    lu = node.available_args(tr)
    args = [13, 1]
    legal = node.transform(tr, *args)

    with futures.ThreadPoolExecutor(max_workers=4) as executor:
        fs = [executor.submit(func, *arg) for arg in enumerate(times[:])]
        print("-- scheduled --")
        while fs:
            done = [f for f in fs if f.done()]
            for f in done:
                print(f"{f.result()=}")
                del fs[fs.index(f)]
    app.compile()
    app = app.generate_code()
    app.compile()
