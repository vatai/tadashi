from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_means_vars(files):
    means = {}
    vars = {}
    for file in files:
        times = np.load(file)
        mean = times.mean(axis=0)
        var = times.var(axis=0)
        name = file.with_suffix("").name
        means[name] = mean
        vars[name] = var
    return pd.DataFrame(means), pd.DataFrame(vars)


def main():
    files = Path("./times/").glob("*.npy")
    means, vars = get_means_vars(files)
    print(means)
    print(means.index)
    labels = [
        "Chosing the transformations",
        "Transforming the schedule",
        "Generating code",
        "Compiling",
        "Execution time",
    ]
    means = means.set_axis(labels=labels)
    means = means.transpose()
    means = means.drop(labels=[labels[0]], axis=1)
    # print(means[[labels[0]]])
    print(means)
    fig, ax = plt.subplots()
    means.plot.bar(stacked=True, ax=ax)
    plt.tight_layout()
    plt.savefig("plot.png")


if __name__ == "__main__":
    main()
