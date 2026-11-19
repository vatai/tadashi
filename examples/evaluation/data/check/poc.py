#!/bin/env python3
import argparse
import re
from ast import literal_eval
from pathlib import Path

from tadashi import translators
from tadashi.apps import Polybench


def parse_out(path):
    benchmark = path.parent.name.split("-seed")[0]
    backend = str(path.parent.parent.name.split("-")[0]).capitalize()
    trs = []
    with open(path) as file:
        for line in file:
            if line.startswith("   ["):
                trs.append(literal_eval(line.strip())[0])
    return [[benchmark, backend, trs]]


def run_tr(benchmark, backend, trs):
    translator = getattr(translators, backend)
    app = Polybench(
        benchmark=benchmark,
        translator=translator(),
        compiler_options=[
            "-O3",
            "-fopenmp",
            "-DEXTRALARGE_DATASET",
            "-DPOLYBENCH_DUMP_ARRAYS",
        ],
    )
    app.compile()
    original = app.dump_arrays()
    app.transform_list(trs)
    tapp = app.generate_code()
    tapp.compile()
    if original != tapp.dump_arrays():
        print("<<< ng >>>", benchmark, trs)
    else:
        print(">>> OK <<<", benchmark, trs)


def main(root, benchmark):
    for path in sorted(root.glob(f"**/{benchmark}*/*.stdout")):
        print(path)
        gens = parse_out(path)
        if gens:
            run_tr(*gens[-1])

    print("done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default=Path("durbin"))
    parser.add_argument("--root", type=Path, default=Path("poc"))
    args = parser.parse_args()
    main(args.root, args.benchmark)
