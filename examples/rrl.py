#!/usr/bin/env python

import ctypes
import random

from tadashi.apps import Simple
from tadashi.tadashilib import TRANSFORMATIONS, Scops, Transformation


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
        print(tr.valid(node))
        while not tr.valid(node):
            node = self.random_node(scop)
            tr = random.choice(list(TRANSFORMATIONS.values()))
            print(tr.valid(node))

        print(tr)
        args = self.random_args(node, tr)
        node.transform(tr, *args)
        print(tr)

    def random_args(self, node, tr):
        args = []
        for pos, argtype in enumerate(tr.argtypes):
            print(f"{tr.func_name=}")
            match tr.func_name:
                case "full_shift_val":
                    arg = random.randint(-100, 100)
                case "partial_shift_val":
                    lb = [0, -100]
                    ub = [len(node.loop_signature) - 1, 100]
                    arg = random.randint(lb[pos], ub[pos])
                case "full_shift_var":
                    num_vars = [len(stmt["vars"]) for stmt in node.loop_signature]
                    print(num_vars)
                case "partial_shift_var":
                    print(tr.func_name)
                case "full_shift_param":
                    print(tr.func_name)
                case "partial_shift_param":
                    print(tr.func_name)
                case "tile":
                    arg = random.randint(1, 1000)
            args.append(arg)
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