#!/bin/env python
import argparse
import json
from pathlib import Path

import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import winter as cm
from scipy.stats import gmean

plt.rcParams["text.latex.preamble"] = (
    # r"\usepackage{libertine}\usepackage{zi4}\usepackage{newtxmath}"
    r"\usepackage{newtxtext,bm}\usepackage[cmintegrals]{newtxmath}"
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


fontsize = 12


def read_poc_output(path):
    f = open(path).readlines()
    names = []
    bl = []
    post = []
    for line_i in range(len(f)):
        if "[STARTING NEW APP]" in f[line_i]:
            if ".orig" in f[line_i + 1]:
                continue
            app_name = f[line_i + 1]
            if ": " in f[line_i + 3]:
                app_baseline = f[line_i + 3]
            else:
                app_baseline = f[line_i + 4]
            i = line_i
            while not "[FINISHED APP]" in f[i]:
                i += 1
            app_post = f[i - 1]
            # print("---------")
            # print(app_name)
            # print(app_baseline)
            # print(app_post)
            names.append(app_name.strip().split("/")[-1])
            bl.append(float(app_baseline.strip().split(": ")[1]))
            post.append(float(app_post.strip().split(": ")[1]))
    baseline = np.array(bl)
    post = np.array(post)
    names = np.array(names)
    idcs = np.argsort(names)
    df = pd.DataFrame([names[idcs], baseline[idcs], post[idcs]])
    df = df.transpose()
    df.rename(columns={1: "baseline", 2: "poc"}, inplace=True)
    df.set_index(0, inplace=True)
    df.index.name = "benchmark"
    return df


def get_ratios(baseline, post, labels):
    # Filter: keep only values where at least one is >= 0.01
    mask = ~((baseline < 0.01) & (post < 0.01))
    # mask = array1 >= 0.001

    for l in sorted(labels):
        if not l in np.array(labels)[mask]:
            print(l)

    baseline = baseline[mask]
    post = post[mask]
    labels = np.array(labels)[mask]

    ratios = baseline / post

    sorted_indices = np.argsort(labels)
    # labels = labels[sorted_indices]
    # ratios = ratios[sorted_indices]
    ratios = np.array([r if r > 1 else 1 for r in ratios])
    print(ratios)
    return ratios, labels


def get_pluto(path):
    data = {}
    for line in open(path):
        if ":::" in line:
            benchmark, rep, time = line.split(":::")
            if benchmark in data:
                old = data[benchmark]
                new = float(time)
                data[benchmark] = new if new < old else old
            else:
                data[benchmark] = float(time)

    df = pd.DataFrame(data, index=[0])
    df = df.transpose()
    df.rename(columns={0: "pluto"}, inplace=True)
    df.index.name = "benchmark"
    # print(f"{df=}")
    return df


def get_evol():
    evol_dir = Path(__file__).parent.parent / "evol"
    results = {}
    for file in evol_dir.glob("*.txt"):
        name_with_num = file.with_suffix("").name
        dash = name_with_num.rfind("-")
        name = name_with_num[:dash]
        lines = file.read_text().split("\n")
        baseline = -float(lines[3].split(":")[1])
        evol = -float(lines[-2].split("---")[1])
        results[name] = [baseline, evol]
    df = pd.DataFrame(results).transpose()
    df.rename(columns={0: "evol_baseline", 1: "evol"}, inplace=True)
    df.index.name = "benchmark"
    return df


def main(poc_path, pluto_path=None, mcts_path=None):
    data = read_poc_output(poc_path)
    if pluto_path:
        data = data.merge(get_pluto(pluto_path), on="benchmark", how="outer")
    if mcts_path:
        mcts_data = pd.read_csv(mcts_path, index_col=0)
        data = data.merge(mcts_data, on="benchmark", how="outer")
    # data = data.merge(get_evol(), on="benchmark", how="outer")
    # print(data)

    x = np.arange(len(data))
    fig, ax = plt.subplots()

    # Reference line at ratio = 1
    ax.axhline(y=1.0, color="#ff6961", linestyle="--", linewidth=2)
    ax.axhline(y=2.0, color="lightgray", linestyle="-", linewidth=1)
    ax.axhline(y=5.0, color="lightgray", linestyle="-", linewidth=1)
    ax.axhline(y=10.0, color="lightgray", linestyle="-", linewidth=1)

    # Plot colored ratio bars
    width = 0.6 / 2
    fix = width
    kwargs = {"edgecolor": "black", "linewidth": 0.3, "zorder": 2}
    if pluto_path:
        pluto = (data["baseline"] / data["pluto"]).to_numpy().astype(np.float64)
        bars = ax.bar(
            x + 0 * width - fix,
            pluto,
            width,
            label="Pluto",
            color=cm(10),
            **kwargs,
        )
        pluto[np.isnan(pluto)] = 1
        print(f"{gmean(pluto)=}")
    poc = (data["baseline"] / data["poc"]).to_numpy().astype(np.float64)
    poc[data["baseline"] < data["poc"]] = 1  # poc doesn't do this so we do it here
    bars = ax.bar(
        x + 1 * width - fix,
        poc,
        width,
        label="Heuristic",
        color=cm(150),
        **kwargs,
    )
    poc[np.isnan(poc)] = 1
    print(f"{gmean(poc)=}")
    if mcts_path:
        mcts = data["mcts"].to_numpy().astype(np.float64)  # this is already speedup
        bars = ax.bar(
            x + 2 * width - fix,
            mcts,
            width,
            label="MCTS",
            color=cm(300),
            **kwargs,
        )
        mcts[np.isnan(mcts)] = 1
        print(f"{gmean(mcts)=}")
    # bars = ax.bar(x + 3 * width - fix, evol, width, label="EVOL", **kwargs)
    # bars = ax.bar(x+width/2, ratios, width / 2, color=bar_colors, edgecolor="black", zorder=2)
    ax.legend()

    # Labels and formatting
    ax.set_ylabel("Speedup (log scale)", fontsize=fontsize)
    ax.set_title("")
    ax.set_xticks(x)
    ax.set_xticklabels(data.index, rotation=90, fontsize=fontsize - 2)
    ax.set_yticks([0.5, 1, 2, 5, 10, 20])
    # ax.legend()

    ax.set_yscale("log")
    # Log scale (optional)
    ax.set_yticks([1, 2, 5, 10, 20])  # You can adjust the range as needed
    ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_ylim(ymin=0.01, ymax=350)

    # Display the plot
    plt.tight_layout()
    sm = ""
    if "_st.sh" in poc_path:
        sm = "s"
    if "_mt.sh" in poc_path:
        sm = "m"
    output_file = f"{sm}t_improvements.pdf"
    print(f"{output_file=}")
    plt.savefig(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("poc", type=str)
    parser.add_argument("--pluto")
    parser.add_argument("--mcts")
    args = parser.parse_args()
    main(args.poc, args.pluto, args.mcts)
