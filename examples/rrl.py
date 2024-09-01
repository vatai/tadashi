#!/usr/bin/env python

import ctypes
import random
from enum import Enum

from tadashi.apps import Simple
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
        return self.node_idx, key, args

    def random_args(self, node, tr):
        print(f"{tr=}")
        lubs = tr.lower_upper_bounds(node)
        print(f"{lubs=}")
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


def main():
    app = Simple("./examples/depnodep.c")
    app.compile()

    t = app.measure()
    print(f"Base time: {t}")
    scops = Scops(app)
    model = Model()

    for _ in range(3):
        node_idx, tr_key, args = model.random_transform(scops[0])
        print(f"node_idx: {node_idx}, tr: {tr_key}, args: {args}")
        tr = TRANSFORMATIONS[tr_key]
        scops[0].schedule_tree[node_idx].transform(tr, *args)
        scops.generate_code(input_path=app.source, output_path=app.alt_source)
        app.compile()
        t = app.measure(timeout=20)
        print(f"WALLTIME: {t}")


if __name__ == "__main__":
    main()
