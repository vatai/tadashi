#!/usr/bin/env python
import argparse
import difflib
import itertools
import json
import random
import subprocess
import time
from pathlib import Path
from subprocess import TimeoutExpired

from tadashi import Scop, TrEnum
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
        default=42,
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
        exps = [2**e for e in range(3, 12)]
        if tr is TrEnum.TILE1D:
            args = [[e] for e in exps]
        elif tr is TrEnum.TILE2D:
            args = [list(e) for e in itertools.product(exps, exps)]
        elif tr is TrEnum.TILE3D:
            args = [list(e) for e in itertools.product(exps, exps, exps)]
        else:
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
    print("Compiling original app... ", end="", flush=True)
    app.compile()
    print("DONE!")
    timer.time("Compilation")
    print("Running original app... ", end="", flush=True)
    t = app.measure()
    print("DONE!")
    timer.time("Total walltime")
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
        print(f"{tr}, ", end="", flush=True)
        legal = scop.transform_list([tr])[-1]
        print(f"# {legal}")
        if legal:
            trs.append(tr)
        timer.time("Transformation + legality")
    print(f"Executing final tr {app.source.name}... ", end="", flush=True)
    scop.reset()
    scop.transform_list(trs)
    print("DONE!")
    timer.reset()
    # print(scop.schedule_tree[trs[-1][0]].yaml_str)
    # print(f"{trs=}")
    print("Generating code... ", end="", flush=True)
    tapp = app.generate_code()
    print("DONE!")
    timer.time("Code generation")
    print("Compiling... ", end="")
    tapp.compile()
    print("DONE!")
    timer.time("Compilation")
    print(f"Running benchmark {app.source.name}... ", end="", flush=True)
    try:
        t = tapp.measure(timeout=10)
        timer.time("Total walltime")
        timer.custom("Kernel walltime", t)
    except TimeoutExpired as e:
        print(f"Timeout expired: {e=}", end="")
    print("DONE!")
    filename = f"./times/{name}-{num_steps}.json"
    json.dump(timer.times, open(filename, "w"))
    print(f"Written: {filename}")


def measure_polybench(num_steps):
    base = Path("examples/polybench")
    for i, p in enumerate(Polybench.get_benchmarks(base)):
        print(f"Loading {p.name}...", end="")
        app = Polybench(p, base, compiler_options=["-DSMALL_DATASET"])
        print("DONE!")
        run_model(app, num_steps=num_steps, name=p.name)


def verify_polybench():
    compiler_options = ["-DSMALL_DATASET", "-DPOLYBENCH_DUMP_ARRAYS"]
    base = Path("examples/polybench")
    for p in Polybench.get_benchmarks(base):
        app = Polybench(p, base, compiler_options)
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
