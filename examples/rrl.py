#!/usr/bin/env python
import random
import time
from datetime import timedelta
from pathlib import Path
from subprocess import TimeoutExpired

import numpy as np
from tadashi.apps import Polybench, Simple
from tadashi.tadashilib import (TRANSFORMATIONS, AstLoopType, LowerUpperBound,
                                Scops, TrEnum)


class Model:
    def __init__(self):
        self.node_idx = 0

    def random_node(self, scop):
        node_idx_inc = random.choice([-1, 0, 1])
        self.node_idx += node_idx_inc
        self.node_idx = max(self.node_idx, 1)
        self.node_idx = min(self.node_idx, len(scop.schedule_tree) - 1)
        return scop.schedule_tree[self.node_idx]

    def random_transform(self, scop):
        node = self.random_node(scop)
        key, tr = random.choice(list(TRANSFORMATIONS.items()))

        while not tr.valid(node):
            node = self.random_node(scop)
            key, tr = random.choice(list(TRANSFORMATIONS.items()))

        args = self.random_args(node, tr)
        return self.node_idx, key, tr, args

    def random_args(self, node, tr):
        if tr == TRANSFORMATIONS[TrEnum.TILE]:
            tile_size = random.choice([2**x for x in range(5, 20)])
            return [tile_size]
        lubs = tr.lower_upper_bounds(node)
        args = []
        for lub in lubs:
            if isinstance(lub, LowerUpperBound):
                lb, ub = lub
                if lb is None:
                    lb = -64
                if ub is None:
                    ub = 64
                args.append(random.randrange(lb, ub))
            else:
                chosen_enum = random.choice(list(lub))
                args.append(chosen_enum.value)

        return args


def run_model(app, num_steps, name=""):
    if name:
        print(f"Running: {name}")
    app.compile()

    t = app.measure()
    print(f"Base time: {t}")
    loop_nests = Scops(app)
    model = Model()

    times = np.zeros([num_steps, 5])
    print(f"{times.shape=}")
    for i in range(num_steps):
        t0 = time.monotonic()
        loop_idx, tr, key, args = model.random_transform(loop_nests[0])
        print(f"loop_idx: {loop_idx}, tr: {key}, args: {args}")
        t1 = time.monotonic()
        times[i, 0] = t1 - t0
        legal = loop_nests[0].schedule_tree[loop_idx].transform(tr, *args)
        if not legal:
            loop_nests[0].schedule_tree[loop_idx].rollback()
        t2 = time.monotonic()
        times[i, 1] = t2 - t1
        loop_nests.generate_code(
            input_path=app.source_path, output_path=app.alt_source_path
        )
        t3 = time.monotonic()
        times[i, 2] = t3 - t2
        app.compile()
        t4 = time.monotonic()
        times[i, 3] = t4 - t3
        try:
            t = app.measure(timeout=10)
            print(f"WALLTIME: {t}")
        except TimeoutExpired as e:
            print(f"Timeout expired: {e=}")
        print(f"{legal=}")
        t5 = time.monotonic()
        times[i, 4] = t5 - t4
    np.save(f"times/{name}.npy", times)


def run_simple():
    run_model(Simple("./examples/depnodep.c"))


def measure_polybench():
    base = Path("build/_deps/polybench-src/")
    # for p in base.glob("**"):
    compiler_options = ["-DSMALL_DATASET"]
    for p in list(base.glob("**"))[:10]:
        if Path(p / (p.name + ".c")).exists():
            app = Polybench(p.relative_to(base), base, compiler_options)
            run_model(app, num_steps=2, name=p.name)
            print("")


def verify_poly():
    pass


if __name__ == "__main__":
    measure_polybench()
