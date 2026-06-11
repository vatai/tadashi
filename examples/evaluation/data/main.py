#!/usr/bin/env python3

import argparse
from pathlib import Path


def fun(path: Path):
    print(path)
    print(path.exists())


def visit_st_mt(path: Path, fun):
    st = path / f"st-{path.name}"
    st_data = fun(st)
    mt = path / f"mt-{path.name}"
    mt_data = fun(mt)
    return {st.name: st_data, mt.name: mt_data}


def get_pluto_data(path):
    # LAST
    print(list(path.glob("*")))


def get_poc_data(path):
    visit_st_mt(path, fun)


def get_evo_data(path):
    visit_st_mt(path, fun)


def get_mcts_data(path):
    visit_st_mt(path, fun)


def main(pluto: Path, poc: Path, evo: Path, mcts: Path):
    pluto_data = get_pluto_data(pluto)
    poc_data = get_poc_data(poc)
    evo_data = get_evo_data(evo)
    mcts_data = get_mcts_data(mcts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pluto", default="pluto", type=Path)
    parser.add_argument("--poc", default="poc", type=Path)
    parser.add_argument("--evo", default="evo", type=Path)
    parser.add_argument("--mcts", default="mcts", type=Path)
    args = parser.parse_args()
    main(args.pluto, args.poc, args.evo, args.mcts)
