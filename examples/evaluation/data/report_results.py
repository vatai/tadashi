#!/usr/bin/env python3
"""Summarize normalized results and generate matplotlib figures."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def read_table(input_dir: Path, name: str) -> pd.DataFrame:
    path = input_dir / f"{name}.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def label_methods(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["method_label"] = (
        result["experiment"].fillna("").astype(str).str.rstrip("/")
        + "/"
        + result["method"].astype(str)
    ).str.lstrip("/")
    return result


def evolution_speedups(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame(columns=["method", "benchmark", "speedup"])
    result = data.copy()
    result["base"] = pd.to_numeric(result["base"], errors="coerce")
    result["seconds"] = pd.to_numeric(result["seconds"], errors="coerce")
    result["speedup"] = np.divide(result["base"], result["seconds"])
    result = result.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["speedup"]
    )
    result["method"] = "evolution-" + result["compiler"].astype(str)
    return result[["method", "benchmark", "speedup"]]


def runtime_speedups(
    transformed_runs: pd.DataFrame,
    original_runs: pd.DataFrame,
    method_prefix: str,
) -> pd.DataFrame:
    if transformed_runs.empty or original_runs.empty:
        return pd.DataFrame(columns=["method", "benchmark", "speedup"])
    transformed = transformed_runs.copy()
    original = original_runs.copy()
    transformed["seconds"] = pd.to_numeric(
        transformed["seconds"], errors="coerce"
    )
    original["seconds"] = pd.to_numeric(original["seconds"], errors="coerce")
    paired = original.merge(
        transformed,
        on=["benchmark", "compiler"],
        how="inner",
        suffixes=("_original", "_transformed"),
    )
    paired["speedup"] = np.divide(
        paired["seconds_original"], paired["seconds_transformed"]
    )
    paired = paired.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["speedup"]
    )
    paired["method"] = method_prefix + paired["compiler"].astype(str)
    return paired[["method", "benchmark", "speedup"]]


def mcts_speedups(mcts_runs: pd.DataFrame) -> pd.DataFrame:
    if mcts_runs.empty:
        return pd.DataFrame(columns=["method", "benchmark", "speedup"])
    result = mcts_runs.copy()
    result["base"] = pd.to_numeric(result["base"], errors="coerce")
    result["seconds"] = pd.to_numeric(result["seconds"], errors="coerce")
    result["speedup"] = np.divide(result["base"], result["seconds"])
    result = result.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["speedup"]
    )
    result["method"] = "mcts-" + result["compiler"].astype(str)
    return result[["method", "benchmark", "speedup"]]


def poc_speedups(poc_runs: pd.DataFrame) -> pd.DataFrame:
    if poc_runs.empty:
        return pd.DataFrame(columns=["method", "benchmark", "speedup"])
    result = poc_runs.copy()
    result["base"] = pd.to_numeric(result["base"], errors="coerce")
    result["seconds"] = pd.to_numeric(result["seconds"], errors="coerce")
    result["speedup"] = np.divide(result["base"], result["seconds"])
    result = result.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["speedup"]
    )
    result["method"] = "poc-" + result["compiler"].astype(str)
    return result[["method", "benchmark", "speedup"]]


def pluto_speedups(
    plutor_runs: pd.DataFrame, original_runs: pd.DataFrame
) -> pd.DataFrame:
    return runtime_speedups(plutor_runs, original_runs, "pluto-")


def combine_speedups(input_dir: Path) -> pd.DataFrame:
    original_runs = read_table(input_dir, "original_runs")
    results = pd.concat(
        [
            evolution_speedups(read_table(input_dir, "evolution_runs")),
            mcts_speedups(read_table(input_dir, "mcts_runs")),
            poc_speedups(read_table(input_dir, "poc_runs")),
            pluto_speedups(
                read_table(input_dir, "plutor_runs"),
                original_runs,
            ),
        ],
        ignore_index=True,
    )
    results["speedup"] = pd.to_numeric(results["speedup"], errors="coerce")
    return results.dropna(subset=["speedup"]).sort_values(["benchmark", "method"])


def build_merged(input_dir: Path) -> pd.DataFrame:
    keys = ["benchmark", "compiler"]

    def times(name: str, columns: dict[str, str]) -> pd.DataFrame:
        data = read_table(input_dir, name)
        if data.empty:
            return pd.DataFrame(columns=keys + list(columns.values()))
        selected = data[keys + list(columns)].rename(columns=columns)
        for column in columns.values():
            selected[column] = pd.to_numeric(selected[column], errors="coerce")
        return selected

    original = times("original_runs", {"seconds": "orignial-time"})
    pluto = times("plutor_runs", {"seconds": "pluto-time"})
    mcts = times(
        "mcts_runs",
        {"base": "mcts-init-time", "seconds": "mcts-time"},
    )
    poc = times(
        "poc_runs",
        {"base": "poc-init-time", "seconds": "poc-time"},
    )
    evolution = times(
        "evolution_runs",
        {"base": "evo-init-time", "seconds": "evo-time"},
    )

    merged = original
    for data in (pluto, mcts, poc, evolution):
        merged = merged.merge(data, on=keys, how="outer")

    merged["pluto-speedup"] = np.divide(
        merged["orignial-time"], merged["pluto-time"]
    )
    merged["mcts-speedup"] = np.divide(
        merged["mcts-init-time"], merged["mcts-time"]
    )
    merged["mcts-speedup-to-original"] = np.divide(
        merged["orignial-time"], merged["mcts-time"]
    )
    merged["poc-speedup"] = np.divide(
        merged["poc-init-time"], merged["poc-time"]
    )
    merged["poc-speedup-to-original"] = np.divide(
        merged["orignial-time"], merged["poc-time"]
    )
    merged["evo-speedup"] = np.divide(
        merged["evo-init-time"], merged["evo-time"]
    )
    merged["evo-speedup-to-original"] = np.divide(
        merged["orignial-time"], merged["evo-time"]
    )
    columns = keys + [
        "orignial-time",
        "pluto-time",
        "pluto-speedup",
        "mcts-init-time",
        "mcts-time",
        "mcts-speedup",
        "mcts-speedup-to-original",
        "poc-init-time",
        "poc-time",
        "poc-speedup",
        "poc-speedup-to-original",
        "evo-init-time",
        "evo-time",
        "evo-speedup",
        "evo-speedup-to-original",
    ]
    return (
        merged.replace([np.inf, -np.inf], np.nan)[columns]
        .sort_values(keys)
        .reset_index(drop=True)
    )


def build_abs_speedup(input_dir: Path) -> pd.DataFrame:
    def fastest(name: str, output_column: str) -> pd.DataFrame:
        data = read_table(input_dir, name)
        if data.empty:
            return pd.DataFrame(columns=["benchmark", output_column])
        data = data.copy()
        data["seconds"] = pd.to_numeric(data["seconds"], errors="coerce")
        return (
            data.dropna(subset=["seconds"])
            .groupby("benchmark", as_index=False)["seconds"]
            .min()
            .rename(columns={"seconds": output_column})
        )

    result = fastest("original_runs", "original-time")
    methods = [
        ("plutor_runs", "pluto"),
        ("poc_runs", "poc"),
        ("mcts_runs", "mcts"),
        ("evolution_runs", "evo"),
    ]
    for table_name, method in methods:
        result = result.merge(
            fastest(table_name, f"{method}-time"),
            on="benchmark",
            how="outer",
        )
        result[f"{method}-speedup"] = np.divide(
            result["original-time"], result[f"{method}-time"]
        )

    columns = ["benchmark", "original-time"]
    for _, method in methods:
        columns.extend([f"{method}-time", f"{method}-speedup"])
    return (
        result.replace([np.inf, -np.inf], np.nan)[columns]
        .sort_values("benchmark")
        .reset_index(drop=True)
    )


def geometric_mean(values: pd.Series) -> float:
    array = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    array = array[np.isfinite(array) & (array > 0)]
    return float(np.exp(np.log(array).mean())) if array.size else np.nan


def summarize(results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if results.empty:
        return (
            pd.DataFrame(
                columns=["method", "benchmarks", "geometric_mean", "median", "best"]
            ),
            pd.DataFrame(columns=["benchmark", "best_method", "speedup"]),
        )
    summary = (
        results.groupby("method")
        .agg(
            benchmarks=("benchmark", "nunique"),
            geometric_mean=("speedup", geometric_mean),
            median=("speedup", "median"),
            best=("speedup", "max"),
        )
        .reset_index()
        .sort_values("geometric_mean", ascending=False)
    )
    winner_indices = results.groupby("benchmark")["speedup"].idxmax()
    winners = (
        results.loc[winner_indices]
        .sort_values("benchmark")
        .reset_index(drop=True)
        .rename(columns={"method": "best_method"})
    )
    return summary, winners


def plot_speedups(results: pd.DataFrame, output: Path) -> None:
    table = results.pivot(index="benchmark", columns="method", values="speedup")
    table = table.sort_index()
    width = max(12, 0.45 * len(table))
    fig, ax = plt.subplots(figsize=(width, 6))
    table.plot(kind="bar", ax=ax, width=0.85)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yscale("log")
    ax.set_ylabel("Speedup over baseline (log scale)")
    ax.set_xlabel("Benchmark")
    ax.legend(title="Method", fontsize=8, ncol=2)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "speedups.png", dpi=180)
    fig.savefig(output / "speedups.pdf")
    plt.close(fig)


def plot_abs_speedup(data: pd.DataFrame, output: Path) -> None:
    if data.empty:
        return
    columns = {
        "pluto-speedup": "Pluto",
        "poc-speedup": "POC",
        "mcts-speedup": "MCTS",
        "evo-speedup": "Evolution",
    }
    table = (
        data.set_index("benchmark")[list(columns)]
        .rename(columns=columns)
        .sort_index()
    )
    width = max(12, 0.45 * len(table))
    fig, ax = plt.subplots(figsize=(width, 6))
    table.plot(kind="bar", ax=ax, width=0.85)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_yscale("log")
    ax.set_ylabel("Absolute speedup over fastest original (log scale)")
    ax.set_xlabel("Benchmark")
    ax.legend(title="Method", fontsize=9, ncol=4)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output / "abs-speedup.png", dpi=180)
    fig.savefig(output / "abs-speedup.pdf")
    plt.close(fig)


def plot_evolution(input_dir: Path, output: Path) -> None:
    data = read_table(input_dir, "evolution_generations")
    if data.empty:
        return
    data = label_methods(data)
    data["generation"] = pd.to_numeric(data["generation"], errors="coerce")
    data["speedup"] = pd.to_numeric(data["speedup"], errors="coerce")
    curves = (
        data.dropna(subset=["generation", "speedup"])
        .groupby(["method_label", "generation"])["speedup"]
        .agg(geometric_mean)
        .unstack("method_label")
    )
    fig, ax = plt.subplots(figsize=(9, 5))
    curves.plot(ax=ax, marker="o")
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Geometric-mean speedup")
    ax.grid(alpha=0.25)
    ax.legend(title="Method", fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "evolution_progress.png", dpi=180)
    fig.savefig(output / "evolution_progress.pdf")
    plt.close(fig)


def plot_mcts(input_dir: Path, output: Path) -> None:
    data = read_table(input_dir, "mcts_progress")
    if data.empty:
        return
    data = label_methods(data)
    data["evaluations"] = pd.to_numeric(data["evaluations"], errors="coerce")
    data["speedup"] = pd.to_numeric(data["speedup"], errors="coerce")
    fig, ax = plt.subplots(figsize=(9, 5))
    for method, group in data.dropna(
        subset=["evaluations", "speedup"]
    ).groupby("method_label"):
        curve = group.groupby("evaluations")["speedup"].agg(geometric_mean)
        ax.step(curve.index, curve.values, where="post", label=method)
    ax.axhline(1.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Evaluations")
    ax.set_ylabel("Geometric-mean speedup")
    ax.grid(alpha=0.25)
    ax.legend(title="Method", fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "mcts_progress.png", dpi=180)
    fig.savefig(output / "mcts_progress.pdf")
    plt.close(fig)


def markdown_table(data: pd.DataFrame, float_columns: set[str]) -> list[str]:
    headers = [str(column) for column in data.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---:" if name in float_columns else "---" for name in headers) + "|",
    ]
    for row in data.itertuples(index=False, name=None):
        cells = []
        for name, value in zip(headers, row):
            if name in float_columns and pd.notna(value):
                cells.append(f"{float(value):.3f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def create_report(
    summary: pd.DataFrame, winners: pd.DataFrame, output: Path
) -> None:
    display_summary = summary.rename(
        columns={
            "method": "Method",
            "benchmarks": "Benchmarks",
            "geometric_mean": "Geometric mean",
            "median": "Median",
            "best": "Best",
        }
    )
    display_winners = winners[["benchmark", "best_method", "speedup"]].rename(
        columns={
            "benchmark": "Benchmark",
            "best_method": "Best method",
            "speedup": "Speedup",
        }
    )
    lines = [
        "# Evaluation Results",
        "",
        "For repeated runs, the best observed speedup is used per method and benchmark.",
        "",
        "## Method Summary",
        "",
        *markdown_table(
            display_summary, {"Geometric mean", "Median", "Best"}
        ),
        "",
        "## Per-Benchmark Winners",
        "",
        *markdown_table(display_winners, {"Speedup"}),
        "",
        "## Figures",
        "",
        "![Absolute speedups](abs-speedup.png)",
        "",
        "![Per-benchmark speedups](speedups.png)",
        "",
        "![Evolution progress](evolution_progress.png)",
        "",
        "![MCTS progress](mcts_progress.png)",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def analyze(input_dir: Path, output: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    output.mkdir(parents=True, exist_ok=True)
    results = combine_speedups(input_dir)
    merged = build_merged(input_dir)
    abs_speedup = build_abs_speedup(input_dir)
    summary, winners = summarize(results)
    merged.to_csv(output / "merged.csv", index=False)
    abs_speedup.to_csv(output / "abs-speedup.csv", index=False)
    results.to_csv(output / "speedups.csv", index=False)
    summary.to_csv(output / "method_summary.csv", index=False)
    winners.to_csv(output / "benchmark_winners.csv", index=False)
    plot_abs_speedup(abs_speedup, output)
    plot_speedups(results, output)
    plot_evolution(input_dir, output)
    plot_mcts(input_dir, output)
    create_report(summary, winners, output)
    print(f"methods: {summary.shape[0]}")
    print(f"benchmarks: {results['benchmark'].nunique()}")
    print(f"analysis output: {output}")
    return summary, winners


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=script_dir / "analysis",
        help="directory containing normalized CSV files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=script_dir / "analysis",
        help="directory for summary tables, report, and figures",
    )
    args = parser.parse_args()
    analyze(args.input.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
