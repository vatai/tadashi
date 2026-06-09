#!/bin/env python3
import argparse
import re
from ast import literal_eval
from pathlib import Path

from tadashi import translators
from tadashi.apps import Polybench


def parse_evo_out(path):
    benchmark = path.parent.name.split("-seed")[0]
    backend = str(path.parent.parent.name.split("-")[0]).capitalize()
    updating_pattern = re.compile(
        r"^  Updating best_individual to (\[.*\]) --- (.\d*\.\d*)"
    )
    tr_pattern = re.compile(r"tadashi\.TrEnum\.([^,]+)")
    ret = []
    with open(path) as file:
        for line in file:
            m = updating_pattern.match(line)
            if m:
                g = m.groups()
                trs = tr_pattern.sub(lambda t: f'"{t.group(1).strip()}"', g[0]).lower()
                speed = -float(g[1])
                ret.append([benchmark, backend, literal_eval(trs), speed])
    return ret


def run_tr(benchmark, backend, trs, speed):
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
        print(">>> OK <<<", benchmark)


def main(root, benchmark):
    for path in sorted(root.glob(f"**/{benchmark}*/*.out.1.0")):
        print(path)
        gens = parse_evo_out(path)
        if gens:
            run_tr(*gens[-1])

    print("done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default=Path("durbin"))
    parser.add_argument("--root", type=Path, default=Path("after-safe-measure"))
    args = parser.parse_args()
    main(args.root, args.benchmark)
