#!/bin/env python
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# source https://colorkit.co/palette/c7522a-e5c185-fbf2c4-74a892-008585/
COLORS = [
    "#c7522a",
    "#e5c185",
    "#74a892",
]


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
    df.rename(columns={1: "baseline", 2: "Heuristic"}, inplace=True)
    df.set_index(0, inplace=True)
    df.index.name = "benchmark"
    df["Heuristic"] = df["baseline"] / df["Heuristic"]
    df["Heuristic"] = np.maximum(df["Heuristic"], 1)
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
    df.rename(columns={0: "Pluto"}, inplace=True)
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


def summary(data: pd.DataFrame):
    data.drop(columns="baseline", inplace=True)
    argmax = data.to_numpy().astype(np.float64).argmax(axis=1)
    for i, k in enumerate(data.columns):
        nonan = data[k].dropna().astype(np.float64)
        best = int(sum(argmax == i))
        print(f"{best=:2};  gmean({k})={gmean(nonan)}")

    print("")


def plot(ax, data, top):
    # stats
    # results = poc[:]
    # winners = ["Heuristic"]

    # Reference line at ratio = 1
    ax.axhline(y=1.0, color="#ff6961", linestyle="--", linewidth=0.6)
    ax.axhline(y=2.0, color="lightgray", linestyle="-", linewidth=0.3)
    ax.axhline(y=5.0, color="lightgray", linestyle="-", linewidth=0.3)
    ax.axhline(y=10.0, color="lightgray", linestyle="-", linewidth=0.3)
    # Plot colored ratio bars
    x = np.arange(len(data))
    width = 0.6 / 3
    fix = width
    kwargs = {"edgecolor": "black", "linewidth": 0.0, "zorder": 2}
    for i, k in enumerate(["Pluto", "Heuristic", "MCTS"]):
        bars = ax.bar(
            x + i * width - fix,
            data[k],
            width,
            label=k,
            color=COLORS[i],
            **kwargs,
        )
        # results = np.vstack([pluto, results])
        # winners = ["pluto", "Heuristic"]
        # pluto = pluto[data.index != "adi"]  # pluto failed with adi
        # print(f"{gmean(pluto)=}")

    # results = np.nan_to_num(results, nan=0)
    # results = np.argmax(results, axis=0)
    # for i, w in enumerate(winners):
    #     print(f"{w}: {np.sum(results == i)}")

    # Labels and formatting
    ax.set_title("")
    ax.set_yticks([0.5, 1, 2, 5, 10, 20])
    if top:
        ax.set_ylabel("Single-thread speedup", fontsize=fontsize)
        ax.legend(loc="upper left")
        ax.set_xticks(x)
        ax.set_xticklabels("")
        ax.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    else:
        ax.set_ylabel("Multi-thread speedup", fontsize=fontsize)
        ax.set_xticks(x)
        ax.set_xticklabels(data.index, rotation=45, ha="right", fontsize=fontsize - 2)
    # ax.legend()

    ax.set_yscale("log")
    # Log scale (optional)
    ax.set_yticks([1, 2, 5, 10, 20])  # You can adjust the range as needed
    ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_ylim(ymin=0.1, ymax=350)


def combine(poc, pluto, mcts):
    kwargs = {"on": "benchmark", "how": "outer"}
    data = get_pluto(pluto)
    data = data.merge(read_poc_output(poc), **kwargs)
    data = data.merge(pd.read_csv(mcts, index_col=0), **kwargs)
    data["Pluto"] = data["baseline"] / data["Pluto"]
    return data


def main(args):
    sdata = combine(args.spoc, args.spluto, args.smcts)
    mdata = combine(args.mpoc, args.mpluto, args.mmcts)

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(10, 5))
    ax = axes[1]

    plot(axes[0], sdata, top=True)
    summary(sdata)
    plot(axes[1], mdata, top=False)
    summary(mdata)

    # Display the plot
    plt.tight_layout()
    output_file = f"comparison.pdf"
    print(f"{output_file=}")
    plt.savefig(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("spoc", type=Path)
    parser.add_argument("spluto", type=Path)
    parser.add_argument("smcts", type=Path)
    parser.add_argument("mpoc", type=Path)
    parser.add_argument("mpluto", type=Path)
    parser.add_argument("mmcts", type=Path)
    args = parser.parse_args()
    main(args)
