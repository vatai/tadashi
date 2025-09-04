#!/bin/env python
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# https://stackoverflow.com/questions/50976297/reduce-a-panda-dataframe-by-groups
# Direct input

plt.rcParams["text.latex.preamble"] = (
    r"\usepackage{libertine}\usepackage{zi4}\usepackage{newtxmath}"
)
params = {
    "axes.titlesize": 16,
    "axes.labelsize": 16,
    "legend.fontsize": 16,
    "text.usetex": True,
    "font.size": 11,
    "font.family": "libertine",
    # "text.latex.unicode": True,
}
plt.rcParams.update(params)


def get_raw_df(files):
    data = {}
    for file in files:
        name = file.with_suffix("").name
        data[name] = json.load(open(file))
    df = pd.concat({k: pd.DataFrame(v) for k, v in data.items()})
    df.index.names = ["Benchmark", "Step"]
    return df


def get_breakdown_df(files, agg_args, norm):
    df = get_raw_df(files)
    gb = df.groupby(by=["Benchmark"])
    df = gb.agg(agg_args)
    if "Total walltime" in df.columns and "Kernel walltime" in df.columns:
        df["Total walltime (diff)"] = df["Total walltime"] - df["Kernel walltime"]
        df = df.drop(["Total walltime"], axis=1)
    if norm:
        df = (df.T / df.sum(axis=1)).T
    rename = {
        "Total walltime": "Execution time",
        "Kernel walltime": "Kernel execution",
    }
    df = df.rename(columns=rename)
    df.index = df.index.str.replace("-10", "")
    df.index = df.index.str.replace("-1", "")
    return df


def breakdown(files, agg_args, norm, size):
    df = get_breakdown_df(files, agg_args, norm)
    fig, ax = plt.subplots()
    df.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        # color=["#eee", "#bbb", "#999", "#666", "#000"],
        cmap="cool",
    )
    plt.xlabel("")
    if norm:
        plt.ylabel("% of runtime")
    else:
        plt.ylabel("Runtime (sec)")
    plt.title(
        f"{size}-long transformation sequence"
        if size > 1
        else "Primitive transformations"
    )
    plt.tight_layout()
    filename = f"plot-breakdown-{'norm' if norm else 'abs'}-{size}.pdf"
    print(filename)
    plt.savefig(filename)


def breakdowns():
    agg_args = {
        # "Random transformation": "min",
        "Total walltime": "min",
        # "Kernel walltime": "min",
        "Compilation": "min",
        "Code generation": "mean",
        "Transformation + legality": "mean",
        "Extraction": "mean",
    }

    # breakdown(
    #     files=Path("./times/").glob("*-10.json"),
    #     agg_args=agg_args,
    #     norm=True,
    #     size=10,
    # )

    breakdown(
        files=Path("./times/").glob("*-10.json"),
        agg_args=agg_args,
        norm=False,
        size=10,
    )
    # breakdown(
    #     files=Path("./times/").glob("*-1.json"),
    #     agg_args=agg_args,
    #     norm=True,
    #     size=1,
    # )
    breakdown(
        files=Path("./times/").glob("*-1.json"),
        agg_args=agg_args,
        norm=False,
        size=1,
    )


def get_throughput_df(files):
    df = get_raw_df(files)
    gb = df.groupby(by=["Benchmark"])
    agg_args = {
        # "Random transformation": "min",
        # "Total walltime": "min",
        # "Kernel walltime": "min",
        # "Compilation": "min",
        # "Code generation": "mean",
        "Transformation + legality": "sum",
        # "Extraction": "sum",
    }
    df = gb.agg(agg_args)
    df["Throughput"] = 10 / df["Transformation + legality"]
    df.index = df.index.str.replace("-10", "")
    df = df.drop(columns=["Transformation + legality"], axis=1)
    print(df.describe())
    return df


def throughput():
    files = Path("./times/").glob("*-10.json")
    df = get_throughput_df(files)
    fig, ax = plt.subplots()
    df.plot.bar(ax=ax)
    plt.xlabel("")
    plt.ylabel("Iterations per second")
    plt.title("Throughput")
    ax.get_legend().remove()
    plt.tight_layout()
    filename = f"plot-throughput.pdf"
    print(filename)
    plt.savefig(filename)


if __name__ == "__main__":
    breakdowns()
    throughput()
