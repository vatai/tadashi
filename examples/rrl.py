#!/usr/bin/env python

import ctypes
import random
from enum import Enum

from tadashi.apps import Simple
from tadashi.tadashilib import TRANSFORMATIONS, LowerUpperBound, Scops, TrEnum


class Model:
    def __init__(self):
        self.node_idx = 0

    def sample(self):
        pass

    def random_node(self, scop):
        node_idx_inc = random.choice([-1, 0, 1])
        self.node_idx += node_idx_inc
        self.node_idx = max(self.node_idx, 1)
        self.node_idx = min(self.node_idx, len(scop.schedule_tree) - 1)
        return scop.schedule_tree[self.node_idx]

    def random_transform(self, scop):
        node = self.random_node(scop)
        tr = random.choice(list(TRANSFORMATIONS.values()))
        while not tr.valid(node):
            node = self.random_node(scop)
            tr = random.choice(list(TRANSFORMATIONS.values()))

        args = self.random_args(node, tr)
        node.transform(tr, *args)

    def random_args(self, node, tr):
        lubs = tr.lower_upper_bounds(node)
        args = []
        for lub in lubs:
            if isinstance(lub, LowerUpperBound):
                lb, ub = lub
                if lb is None:
                    lb = -100
                if ub is None:
                    ub = 100
                args.append(random.randrange(lb, ub))
            else:
                chosen_enum = random.choice(list(lub))
                args.append(chosen_enum.value)

        return args


def main():
    app = Simple("./examples/depnodep.c")
    scops = Scops(app)
    scop = scops[0]  # select_scop()
    model = Model()

    for _ in range(3):
        model.random_transform(scop)
        scops.generate_code()
        app.compile()
        t = app.measure()
        print(f">>>>>>>>>> {t} <<<<<<<<<<")


if __name__ == "__main__":
    main()
