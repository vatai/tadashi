#!/usr/bin/env python

import random

from tadashi.apps import Simple
from tadashi.tadashilib import TRANSFORMATIONS, Scops, Transformation


class Model:
    def __init__(self):
        self.node_idx = 0

    def sample(self):
        pass

    def random_transform(self, scop):
        node_idx_inc = random.choice([-1, 0, 1])
        self.node_idx += node_idx_inc
        self.node_idx = max(self.node_idx, 0)
        self.node_idx = min(self.node_idx, len(scop.schedule_tree) - 1)
        tr = random.choice([k for k in TRANSFORMATIONS.keys()])
        node = scop.schedule_tree[self.node_idx]
        args = self.random_args(node, tr)
        node.transform(tr, *args)
        print(tr)

    def random_args(node, tr):
        pass


def main():
    app = Simple("./examples/depnodep.c")
    scops = Scops(app)
    scop = scops[0]  # select_scop()
    model = Model()

    for _ in range(20):
        model.random_transform(scop)
        scops.generate_code()
        app.compile()
        app.measure()


if __name__ == "__main__":
    main()
