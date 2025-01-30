from concurrent import futures

import tadashi
from tadashi.apps import App, Simple


def func(app: App, scop_idx: int, transformation_list: list):
    legal = app.scops[scop_idx].transform_list(transformation_list)
    tapp = app.generate_code()
    tapp.compile()
    runtime = tapp.measure()
    return legal, runtime


def main():
    app = Simple("examples/depnodep.c")
    node = app.scops[0].schedule_tree[1]
    tlist = [[0, 1, tadashi.TrEnum.FULL_SHIFT_VAR, 13, 1]]

    with futures.ThreadPoolExecutor(max_workers=4) as executor:
        fs = [executor.submit(app.transform_list, tlist)]
        while fs:
            done = [f for f in fs if f.done()]
            for f in done:
                print(f"{f.result()=}")
                del fs[fs.index(f)]


if __name__ == "__main__":
    main()
