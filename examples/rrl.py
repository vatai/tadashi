#!/usr/bin/env python
import difflib
import json
import random
import subprocess
import time
from pathlib import Path
from subprocess import TimeoutExpired

from tadashi import TRANSFORMATIONS, LowerUpperBound, Scops, TrEnum
from tadashi.apps import Polybench, Simple


def get_polybench_list():
    base = Path("examples/polybench")
    result = []
    for p in base.glob("**"):
        if Path(p / (p.name + ".c")).exists():
            result.append(p.relative_to(base))
    return base, result


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
            tile_size = random.choice([2**x for x in range(5, 12)])
            return [tile_size]
        lubs = tr.available_args(node)
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


class Timer:
    def __init__(self):
        self.times = [{}]
        self.tick = time.monotonic()

    def time(self, key):
        t = time.monotonic()
        self.times[-1][key] = t - self.tick
        self.tick = t

    def reset(self):
        self.tick = time.monotonic()

    def custom(self, key, value):
        self.times[-1][key] = value


def get_array(app: Polybench):
    result = subprocess.run(
        app.run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40
    )
    output = result.stderr.decode()
    return output.split("\n")


def run_model(app, num_steps, name=""):
    model = Model()
    timer = Timer()
    app.compile()
    timer.time("Compilation")
    app.measure()
    t = timer.time("Total walltime")
    scop = app.scops[0]
    timer.time("Extraction")
    timer.custom("Kernel walltime", t)
    for i in range(num_steps):
        timer.times.append({})
        timer.reset()
        loop_idx, tr, key, args = model.random_transform(scop)
        timer.time("Random transformation")
        legal = scop.schedule_tree[loop_idx].transform(tr, *args)
        timer.time("Transformation + legality")
        if not legal:
            scop.schedule_tree[loop_idx].rollback()
    timer.reset()
    app = app.generate_code()
    timer.time("Code generation")
    app.compile()
    timer.time("Compilation")
    try:
        t = app.measure(timeout=60)
        timer.time("Total walltime")
        timer.custom("Kernel walltime", t)
    except TimeoutExpired as e:
        print(f"Timeout expired: {e=}")
    filename = f"./times/{name}-{num_steps}.json"
    json.dump(timer.times, open(filename, "w"))
    print(f"Written: {filename}")


def run_simple():
    run_model(Simple("./examples/depnodep.c"), num_steps=5)


def measure_polybench(num_steps):
    base, poly = get_polybench_list()
    for i, p in enumerate(poly):
        print(f"Start {i+1}. {p.name}")
        app = Polybench(p, base, compiler_options=["-DSMALL_DATASET"])
        run_model(app, num_steps=num_steps, name=p.name)


def verify_polybench():
    base, poly = get_polybench_list()
    compiler_options = ["-DSMALL_DATASET", "-DPOLYBENCH_DUMP_ARRAYS"]
    for p in poly:
        app = Polybench(p, base, compiler_options)
        app.compile()
        gold = get_array(app)
        # print(f"{gold[:3]=}")
        run_model(app, num_steps=3, name=p.name)
        # app.compile()
        mod = get_array(app)
        print(f"{mod [:3]=}")
        diff = "\n".join(difflib.unified_diff(gold, mod))
        if diff:
            print("<<<<<<<<<<<<< ERROR")
            print(diff)
        else:
            print(f">>>>>>>>>>>>> OK {p}")


if __name__ == "__main__":
    random.seed(42)
    # verify_polybench()
    measure_polybench(num_steps=1)
    # measure_polybench(num_steps=10)
