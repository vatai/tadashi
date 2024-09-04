#!/usr/bin/env python
import random
from pathlib import Path
from subprocess import TimeoutExpired

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

        # self.node_idx = 6
        # node = scop.schedule_tree[self.node_idx]
        # key = TrEnum.FULL_FUSE
        # tr = TRANSFORMATIONS[key]

        while not tr.valid(node):
            node = self.random_node(scop)
            key, tr = random.choice(list(TRANSFORMATIONS.items()))

        args = self.random_args(node, tr)
        # args = []
        return self.node_idx, key, args

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


def run_model(app, num_steps=10):
    app.compile()

    t = app.measure()
    print(f"Base time: {t}")
    loop_nests = Scops(app)
    model = Model()

    for _ in range(num_steps):
        loop_idx, transformation_id, args = model.random_transform(loop_nests[0])
        print(f"loop_idx: {loop_idx}, tr: {transformation_id}, args: {args}")
        tr = TRANSFORMATIONS[transformation_id]
        legal = loop_nests[0].schedule_tree[loop_idx].transform(tr, *args)
        print(f"{legal=}")
        loop_nests.generate_code(
            input_path=app.source_path, output_path=app.alt_source_path
        )
        app.compile()
        try:
            t = app.measure(timeout=10)
            print(f"WALLTIME: {t}")
        except TimeoutExpired as e:
            print(f"Timeout expired: {e=}")


def main():
    # run_model(Simple("./examples/depnodep.c"))
    base = Path("build/_deps/polybench-src/")
    for p in base.glob("**"):
        if Path(p / (p.name + ".c")).exists():
            run_model(Polybench(p.relative_to(base), base))


if __name__ == "__main__":
    main()
