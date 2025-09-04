#!/bin/env python
import argparse
import json
from pathlib import Path

import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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


fontsize = 12


def read_poc_output(path):
    f = open(path).readlines()
    names = []
    bl = []
    post = []
    for line_i in range(len(f)):
        if "[STARTING NEW APP]" in f[line_i]:
            app_name = f[line_i + 1]
            app_baseline = f[line_i + 3]
            i = line_i
            while not "32:" in f[i]:
                i += 1
            app_post = f[i]
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


def get_pluto(labels):
    pluto_txt = "../pluto/pluto_times_EXTRALARGE_O3_10.csv"
    df = pd.read_csv(
        pluto_txt,
        sep="\t",
        header=None,
    )
    df.drop(columns=11, inplace=True)
    df.set_index(0, inplace=True)
    df = df.transpose()
    df = df.min()
    df.name = "pluto"
    df.index.name = "benchmark"
    return df


def main(path):
    data = read_poc_output(path)
    data = data.merge(get_pluto(data.index), on="benchmark")

    poc = (data["baseline"] / data["poc"]).to_numpy().astype(np.float64)
    pluto = (data["baseline"] / data["pluto"]).to_numpy().astype(np.float64)
    # Normalize with midpoint at 1
    poc_norm = colors.TwoSlopeNorm(vmin=0, vcenter=1.0, vmax=np.max(poc) / 5)
    poc_colors = cm.coolwarm(poc_norm(poc))

    pluto_norm = colors.TwoSlopeNorm(vmin=0, vcenter=1.0, vmax=np.max(pluto) / 5)
    pluto_colors = cm.vanimo(pluto_norm(pluto))

    x = np.arange(len(data))
    width = 0.6

    fig, ax = plt.subplots()

    # Reference line at ratio = 1
    ax.axhline(y=1.0, color="#ff6961", linestyle="--", linewidth=2)
    ax.axhline(y=2.0, color="lightgray", linestyle="-", linewidth=1)
    ax.axhline(y=5.0, color="lightgray", linestyle="-", linewidth=1)
    ax.axhline(y=10.0, color="lightgray", linestyle="-", linewidth=1)

    # Plot colored ratio bars
    kwargs = {"edgecolor": "black", "linewidth": 0.3, "zorder": 2}
    bars = ax.bar(x, poc, width / 2, label="POC", **kwargs)
    bars = ax.bar(x + width / 2, pluto, width / 2, label="Pluto", **kwargs)
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

    # Display the plot
    plt.tight_layout()
    plt.savefig("poc_improvements.pdf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str)
    args = parser.parse_args()
    main(args.input)
