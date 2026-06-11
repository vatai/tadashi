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
    # if len(lines) != 8:
    #     # print(f"BAD CHECK {path}/{compiler}/{benchmark}")
    #     # print("\n".join(lines))
    for i, line in enumerate(lines):
        if compiler in line:
            return lines[i + 1].startswith(">>> OK <<<")
    return False


def poc1(path: Path):
    result = defaultdict(dict)
    opattern = re.compile(r"Baseline measure: (.*)")
    tpattern = re.compile(r"Tiling with size ([^:]*): (.*)")
    # nt = path.name[:2]
    for p in path.rglob("*.stdout"):
        benchmark = p.parent.name
        compiler = p.parents[1].name
        lines = p.read_text().split("\n")
        otime_str = lines[6]
        entry = {}
        entry["check"] = check_ok(path, benchmark, compiler)
        m = opattern.match(otime_str)
        if m:
            entry["otime"] = float(m.groups()[0])
        ttime_str = lines[-5]
        m = tpattern.match(ttime_str)
        if m:
            g = m.groups()
            entry["tile_size"] = int(g[0])
            entry["ttime"] = float(g[1])
        result[compiler][benchmark] = entry
    return result


def evo1(path: Path):
    result = defaultdict(dict)
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    opattern = re.compile(rf"Measure without transformations:\s*({number})")
    tpattern = re.compile(rf"\s*Fitness on generation\s+(\d+):\s*({number})")
    for p in path.rglob("*.out.1.0"):
        benchmark = p.parent.name.rsplit("-seed", 1)[0]
        compiler = p.parents[1].name
        entry = {"check": check_ok(path, benchmark, compiler)}
        timings = []
        for line in p.read_text().splitlines():
            m = opattern.fullmatch(line)
            if m:
                entry["otime"] = abs(float(m.group(1)))
                continue
            m = tpattern.match(line)
            if m:
                timings.append((abs(float(m.group(2))), int(m.group(1))))
        if timings:
            entry["ttime"], entry["generation"] = min(timings)
        result[compiler][benchmark] = entry
    return result


def mcts1(path: Path):
    result = defaultdict(dict)
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    pattern = re.compile(rf"(initial|optimized) time:\s*({number})")
    check_path = path.with_name(path.name.replace("mcts", "mtcs"))
    for p in path.rglob("*.stdout"):
        benchmark = p.parent.name.rsplit("-seed", 1)[0]
        compiler = p.parents[1].name
        entry = {"check": check_ok(check_path, benchmark, compiler)}
        timings = []
        for line in p.read_text().splitlines():
            m = pattern.fullmatch(line)
            if not m:
                continue
            kind = m.group(1)
            seconds = float(m.group(2))
            if seconds <= 0:
                continue
            if kind == "initial" and "otime" not in entry:
                entry["otime"] = seconds
            timings.append(seconds)
        if timings:
            entry["ttime"] = min(timings)
        result[compiler][benchmark] = entry
    return result


def nested_data_frame(data):
    return pd.concat(
        {
            compiler: pd.DataFrame.from_dict(benchmarks, orient="index")
            for compiler, benchmarks in data.items()
        },
        names=["compiler", "benchmark"],
    )


def visit_st_mt(path: Path, fun):
    st = path / f"st-{path.name}"
    st_data = fun(st)
    mt = path / f"mt-{path.name}"
    mt_data = fun(mt)
    for s in st_data:
        print(s)
    st_df = nested_data_frame(st_data)
    mt_df = nested_data_frame(mt_data)
    return pd.concat({"st": st_df, "mt": mt_df}, names=["nt"])


def get_pluto_data(path):
    # LAST
    print(list(path.glob("*")))


def main(pluto: Path, poc: Path, evo: Path, mcts: Path):
    # pluto_data = get_pluto_data(pluto)
    poc_data = visit_st_mt(poc, poc1)
    evo_data = visit_st_mt(evo, evo1)
    mcts_data = visit_st_mt(mcts, mcts1)
    data = pd.concat(
        {"poc": poc_data, "evo": evo_data, "mcts": mcts_data},
        axis="columns",
    )
    print(data.index.droplevel("benchmark").unique())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pluto", default="pluto", type=Path)
    parser.add_argument("--poc", default="poc", type=Path)
    parser.add_argument("--evo", default="evo", type=Path)
    parser.add_argument("--mcts", default="mcts", type=Path)
    args = parser.parse_args()
    main(args.pluto, args.poc, args.evo, args.mcts)
