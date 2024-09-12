import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# https://stackoverflow.com/questions/50976297/reduce-a-panda-dataframe-by-groups


def get_df(files, agg_args, norm):
    means = {}
    for file in files:
        name = file.with_suffix("").name
        means[name] = json.load(open(file))
    df = pd.concat({k: pd.DataFrame(v) for k, v in means.items()})
    df.index.names = ["benchmark", "step"]
    # print(df)
    gb = df.groupby(by=["benchmark"])
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
    print(df.columns)
    return df


def main(files, agg_args, norm, size):
    df = get_df(files, agg_args, norm)
    fig, ax = plt.subplots()
    df.plot.bar(stacked=True, ax=ax)
    if norm:
        plt.ylabel("% of runtime")
    else:
        plt.ylabel("Runtime")
    plt.title(
        f"Breakdown of {size}-long transformation seq"
        if size > 0
        else "Breakdown of primitive transformations"
    )
    plt.tight_layout()
    filename = f"plot-{'norm' if norm else 'abs'}-{size}.pdf"
    print(filename)
    plt.savefig(filename)


if __name__ == "__main__":
    agg_args = {
        # "Random transformation": "min",
        "Total walltime": "min",
        # "Kernel walltime": "min",
        "Compilation": "min",
        "Code generation": "mean",
        "Transformation + legality": "mean",
        "Extraction": "mean",
    }

    main(
        files=Path("./times/").glob("*-10.json"),
        agg_args=agg_args,
        norm=True,
        size=10,
    )

    main(
        files=Path("./times/").glob("*-10.json"),
        agg_args=agg_args,
        norm=False,
        size=10,
    )
    main(
        files=Path("./times/").glob("*-1.json"),
        agg_args=agg_args,
        norm=True,
        size=1,
    )
    main(
        files=Path("./times/").glob("*-1.json"),
        agg_args=agg_args,
        norm=False,
        size=1,
    )
