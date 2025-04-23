#!/usr/bin/env python
import difflib
import json
import random
import subprocess
import time
from pathlib import Path
from subprocess import TimeoutExpired

from tadashi import TRANSFORMATIONS, LowerUpperBound, Scop, Scops, TrEnum
from tadashi.apps import Polybench, Simple


class Model:
    def __init__(self):
        self.node_idx = 0

    def random_transform(self, scop: Scop):
        node = scop.schedule_tree[self.node_idx]
        indices = [node.parent_idx] if self.node_idx > 0 else []
        self.node_idx = random.choice(indices + node.children_idx)
        node = scop.schedule_tree[self.node_idx]
        while not node.available_transformations:
            indices = [node.parent_idx] if self.node_idx > 0 else []
            self.node_idx = random.choice(indices + node.children_idx)
            node = scop.schedule_tree[self.node_idx]
        tr = random.choice(node.available_transformations)
        args = node.get_args(tr, start=-64, end=64)
        return node, tr, random.choice(args)
        if args:
            return node, tr, random.choice(args)
        else:
            return node, tr, []


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
        node, tr, args = model.random_transform(scop)
        # print(f">>>>> {node=}")
        # print(f">>>>> {tr=}")
        # print(f">>>>> {args=}")
        timer.time("Random transformation")
        legal = node.transform(tr, *args)
        timer.time("Transformation + legality")
        if not legal:
            node.rollback()
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
    run_model(Simple("./examples/inputs/depnodep.c"), num_steps=5)


def measure_polybench(num_steps):
    base = Path("examples/polybench")
    for i, p in enumerate(Polybench.get_benchmarks(base)):
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
