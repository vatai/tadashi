#!/usr/bin/env python3

import argparse
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["text.latex.preamble"] = (
    r"\usepackage{libertine}\usepackage{zi4}\usepackage{newtxmath}"
    # r"\usepackage{newtxtext,bm}\usepackage[cmintegrals]{newtxmath}"
)
plt.rcParams.update(
    {
        "axes.titlesize": 16,
        "axes.labelsize": 16,
        "legend.fontsize": 16,
        "text.usetex": True,
        "font.size": 11,
        "font.family": "libertine",
    }
    # "text.latex.unicode": True,
)

FONTSIZE = 12
# source https://colorkit.co/palette/c7522a-e5c185-fbf2c4-74a892-008585/
COLORS = ["#c7522a", "#e5c185", "#74a892"]
METHOD_LABELS = {"poc": "POC", "evo": "Evolution", "mcts": "MCTS"}


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
    st_df = nested_data_frame(st_data)
    mt_df = nested_data_frame(mt_data)
    return pd.concat({"st": st_df, "mt": mt_df}, names=["nt"])


def get_pluto_data(path):
    # LAST
    print(list(path.glob("*")))


def plot_speedups(speedups: pd.DataFrame, filename: Path):
    methods = list(METHOD_LABELS)
    benchmarks = sorted(speedups.index.get_level_values("benchmark").unique())
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 5))

    for ax, nt in zip(axes, ("st", "mt")):
        plot_data = speedups.loc[nt].reindex(benchmarks).clip(lower=1)

        yticks = [1, 5, 20, 80, 320]
        ax.axhline(y=1.0, color="#ff6961", linestyle="--", linewidth=0.6)
        for y in yticks:
            ax.axhline(y=y, color="lightgray", linestyle="-", linewidth=0.3)

        x = np.arange(len(plot_data))
        width = 0.6 / len(methods)
        offset = width
        for i, method in enumerate(methods):
            ax.bar(
                x + i * width - offset,
                plot_data[method],
                width,
                label=METHOD_LABELS[method],
                color=COLORS[i],
                edgecolor="black",
                linewidth=0.0,
                zorder=2,
            )

        ax.set_ylabel(
            "Single-thread speedup" if nt == "st" else "Multi-thread speedup",
            fontsize=FONTSIZE,
        )
        ax.set_yscale("log")
        ax.set_yticks(yticks)
        ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
        ax.set_ylim(ymin=0.8, ymax=320)
        ax.set_xticks(x)
        if nt == "st":
            ax.legend(loc="upper left")
            ax.set_xticklabels("")
            ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
        else:
            ax.set_xticklabels(
                plot_data.index,
                rotation=45,
                ha="right",
                fontsize=FONTSIZE - 2,
            )

    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)


def main(pluto: Path, poc: Path, evo: Path, mcts: Path):
    # pluto_data = get_pluto_data(pluto)
    poc_data = visit_st_mt(poc, poc1)
    evo_data = visit_st_mt(evo, evo1)
    mcts_data = visit_st_mt(mcts, mcts1)
    data = pd.concat(
        {"poc": poc_data, "evo": evo_data, "mcts": mcts_data},
        axis="columns",
    )
    baseline = data[[("poc", "otime"), ("mcts", "otime")]].min(axis="columns")
    speedups = pd.concat(
        {
            method: pd.DataFrame(
                {
                    "speedup": baseline / data[(method, "ttime")],
                    "checkb": data[(method, "check")],
                }
            )
            for method in ("poc", "evo", "mcts")
        },
        axis="columns",
    )
    valid_speedups = speedups.xs("speedup", axis="columns", level=1).where(
        speedups.xs("checkb", axis="columns", level=1).fillna(False)
    )
    merged = valid_speedups.groupby(level=["nt", "benchmark"]).max()
    polly_llvm21 = valid_speedups.xs("polly-llvm21", level="compiler")
    pet = valid_speedups.xs("pet", level="compiler")
    pet_fcc = valid_speedups.xs("pet-fcc", level="compiler")

    plot_speedups(merged, Path("comparison.pdf"))
    plot_speedups(polly_llvm21, Path("polly-llvm21-comparison.pdf"))
    plot_speedups(pet, Path("pet-comparison.pdf"))
    plot_speedups(pet_fcc, Path("pet-fcc-comparison.pdf"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pluto", default="pluto", type=Path)
    parser.add_argument("--poc", default="poc", type=Path)
    parser.add_argument("--evo", default="evo", type=Path)
    parser.add_argument("--mcts", default="mcts", type=Path)
    args = parser.parse_args()
    main(args.pluto, args.poc, args.evo, args.mcts)
