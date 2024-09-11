import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def get_df(files):
    means = {}
    for file in files:
        name = file.with_suffix("").name
        means[name] = json.load(open(file))
    df = pd.concat({k: pd.DataFrame(v) for k, v in means.items()})
    df.index.names = ["benchmark", "step"]
    # https://stackoverflow.com/questions/50976297/reduce-a-panda-dataframe-by-groups
    df = df.groupby(by=["benchmark"]).agg(
        {
            # "Random transformation": "min",
            "Total walltime": "max",
            "Kernel walltime": "min",
            "Compilation": "min",
            "Code generation": "mean",
            "Transformation + legality": "mean",
            "Extraction": "mean",
        }
    )
    df["Total walltime"] = df["Total walltime"] - df["Kernel walltime"]
    print(df)
    print(df.sum(axis=1))
    df = df.T / df.sum(axis=1)
    print(df)
    return df.T


def main(files):
    means = get_df(list(files)[:3])
    fig, ax = plt.subplots()
    means.plot.bar(stacked=True, ax=ax)
    plt.tight_layout()
    plt.savefig("plot.pdf")


if __name__ == "__main__":
    main(files=Path("./times/").glob("*-10.json"))
