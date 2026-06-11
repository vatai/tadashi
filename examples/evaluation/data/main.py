#!/usr/bin/env python3

import argparse
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd


def check_ok(path: Path, benchmark: str, compiler: str):
    check_base = path.parents[1] / "check" / path.parent.name
    check_files = list(check_base.glob(f"{path.name}-{benchmark}.*"))
    if len(check_files) != 1:
        print(f"{check_files=}")
    lines = check_files[0].read_text().split("\n")
    if len(lines) != 8:
        print(f"BAD CHECK {path}/{compiler}/{benchmark}")
        # print("\n".join(lines))
    for i, line in enumerate(lines):
        if compiler in line:
            return lines[i + 1].startswith(">>> OK <<<")
    return False


def poc1(path: Path):
    result = {}
    opattern = re.compile(r"Baseline measure: (.*)")
    tpattern = re.compile(r"Tiling with size ([^:]*): (.*)")
    # nt = path.name[:2]
    for p in path.rglob("*.stdout"):
        entry = {}
        benchmark = p.parent.name
        compiler = p.parents[1].name
        entry["compiler"] = compiler
        lines = p.read_text().split("\n")
        otime_str = lines[6]
        if not check_ok(path, benchmark, compiler):
            continue
        m = opattern.match(otime_str)
        if m:
            entry["otime"] = float(m.groups()[0])
        ttime_str = lines[-5]
        m = tpattern.match(ttime_str)
        if m:
            g = m.groups()
            entry["tile_size"] = int(g[0])
            entry["ttime"] = float(g[1])
        result[benchmark] = entry
    return result


def visit_st_mt(path: Path, fun):
    st = path / f"st-{path.name}"
    st_data = fun(st)
    mt = path / f"mt-{path.name}"
    mt_data = fun(mt)
    for s in st_data:
        print(s)
    st_df = pd.DataFrame(st_data)
    mt_df = pd.DataFrame(mt_data)
    return


def get_pluto_data(path):
    # LAST
    print(list(path.glob("*")))


def get_poc_data(path):
    return visit_st_mt(path, poc1)


# def get_evo_data(path):
#     visit_st_mt(path, fun)


# def get_mcts_data(path):
#     visit_st_mt(path, fun)


def main(pluto: Path, poc: Path, evo: Path, mcts: Path):
    # pluto_data = get_pluto_data(pluto)
    poc_data = get_poc_data(poc)
    print(poc_data)
    # evo_data = get_evo_data(evo)
    # mcts_data = get_mcts_data(mcts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pluto", default="pluto", type=Path)
    parser.add_argument("--poc", default="poc", type=Path)
    parser.add_argument("--evo", default="evo", type=Path)
    parser.add_argument("--mcts", default="mcts", type=Path)
    args = parser.parse_args()
    main(args.pluto, args.poc, args.evo, args.mcts)
