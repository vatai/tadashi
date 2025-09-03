#!/usr/bin/env python
import argparse
import difflib
import json
import random
import subprocess
import time
from pathlib import Path
from subprocess import TimeoutExpired

from tadashi import Scop
from tadashi.apps import Polybench, Simple


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify",
        default=False,
        help="Verify instead of measure",
        action="store_true",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2,
        help="Random seed",
    )
    parser.add_argument(
        "--num-steps",
        type=int,
        default=1,
        help="Number of transformations",
    )
    return parser.parse_args()


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
        return [node.index, tr, *random.choice(args)]


class Timer:
    def __init__(self):
        self.times = [{}]
        self.tick = time.monotonic()

    def time(self, key):
        t = time.monotonic()
        self.times[-1][key] = t - self.tick
        self.tick = t
        return t

    def reset(self):
        self.tick = time.monotonic()

    def custom(self, key, value):
        self.times[-1][key] = value


def get_array(app: Polybench):
    result = subprocess.run(
        app.run_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=40,
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
    trs = []
    for i in range(num_steps):
        timer.times.append({})
        timer.reset()
        timer.time("Random transformation")
        scop.reset()
        scop.transform_list(trs)
        tr = model.random_transform(scop)
        legal = scop.transform_list([tr])[-1]
        if legal:
            trs.append(tr)
        timer.time("Transformation + legality")
    scop.reset()
    scop.transform_list(trs)
    timer.reset()
    print(f"{trs=}")
    print("transformed")
    tapp = app.generate_code()
    print("code generated")
    timer.time("Code generation")
    tapp.compile()
    print("compiled")
    timer.time("Compilation")
    try:
        t = tapp.measure(timeout=10)
        timer.time("Total walltime")
        timer.custom("Kernel walltime", t)
    except TimeoutExpired as e:
        print(f"Timeout expired: {e=}")
    times_dir = Path("./times")
    times_dir.mkdir(exist_ok=True)
    filename = times_dir / f"{name}-{num_steps}.json"
    json.dump(timer.times, open(filename, "w"))
    print(f"Written: {filename}")


def measure_polybench(num_steps):
    for i, p in enumerate(Polybench.get_benchmarks()):
        print(f"Start {i+1}. {p.name}")
        app = Polybench(p, compiler_options=["-DSMALL_DATASET"])
        print("app done")
        run_model(app, num_steps=num_steps, name=p.name)


def verify_polybench():
    compiler_options = ["-DSMALL_DATASET", "-DPOLYBENCH_DUMP_ARRAYS"]
    for p in Polybench.get_benchmarks():
        app = Polybench(p, compiler_options=compiler_options)
        app.compile()
        gold = get_array(app)
        # print(f"{gold[:3]=}")
        run_model(app, num_steps=3, name=p.name)
        # app.compile()
        mod = get_array(app)
        # print(f"{mod [:3]=}")
        diff = "\n".join(difflib.unified_diff(gold, mod))
        if diff:
            print("<<<<<<<<<<<<< ERROR")
            print(diff)
        else:
            print(f">>>>>>>>>>>>> OK {p}")


if __name__ == "__main__":
    args = get_args()
    random.seed(args.seed)
    if args.verify:
        verify_polybench()
    else:
        measure_polybench(num_steps=args.num_steps)
