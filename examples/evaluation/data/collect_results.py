#!/usr/bin/env python3
"""Collect evaluation logs into normalized pandas DataFrames and CSV files."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
SEED_SUFFIX = re.compile(r"-seed\d+$")
# Binaries are named <benchmark>[.pluto].<dataset>_O<level>.<compiler>[.st|.mt].x
EXECUTABLE_NAME = re.compile(
    r"^(?P<benchmark>[^.]+)(?P<transformed>\.pluto)?"
    r"\.[^.]+_O\d+\.(?P<compiler>[^.]+)(?:\.(?:st|mt))?\.x$"
)
DATASET_NAME = re.compile(r"^[A-Z][A-Z0-9_-]*$")

EVOLUTION_RUN_COLUMNS = [
    "benchmark",
    "compiler",
    "base",
    "seconds",
    "source",
    "line",
]
GENERATION_COLUMNS = [
    "experiment",
    "dataset",
    "configuration",
    "method",
    "benchmark",
    "run",
    "generation",
    "fitness_seconds",
    "speedup",
    "evaluation_seconds",
    "reproduction_seconds",
    "source",
]
MCTS_RUN_COLUMNS = [
    "benchmark",
    "compiler",
    "base",
    "seconds",
    "source",
    "line",
]
POC_RUN_COLUMNS = MCTS_RUN_COLUMNS
MCTS_PROGRESS_COLUMNS = [
    "experiment",
    "dataset",
    "configuration",
    "method",
    "benchmark",
    "run",
    "line",
    "timestamp",
    "rollouts",
    "evaluations",
    "speedup",
    "transform",
    "source",
]
PLUTO_RUN_COLUMNS = [
    "benchmark",
    "compiler",
    "seconds",
    "source",
    "line",
]

CONFIG_COMPILERS = {
    "pet": "gcc",
    "pet-fcc": "fcc",
    "polly-llvm21": "clang-21",
}


def frame(rows: list[dict], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame.from_records(rows, columns=columns)


def run_metadata(path: Path, root: Path) -> dict[str, str]:
    relative = path.relative_to(root)
    parts = relative.parts
    run_dir = path.parent
    dataset_index = next(
        (i for i, part in enumerate(parts) if DATASET_NAME.fullmatch(part)), None
    )
    method_index = len(parts) - 3
    return {
        "experiment": (
            "/".join(parts[:dataset_index])
            if dataset_index is not None
            else parts[0]
        ),
        "dataset": parts[dataset_index] if dataset_index is not None else "",
        "configuration": (
            "/".join(parts[dataset_index + 1 : method_index])
            if dataset_index is not None
            else ""
        ),
        "method": run_dir.parent.name,
        "benchmark": SEED_SUFFIX.sub("", run_dir.name),
        "run": run_dir.name,
        "source": str(relative),
    }


def parse_namespace(line: str) -> dict:
    start = line.find("Namespace(")
    if start < 0:
        return {}
    content = line[start + len("Namespace(") :].rstrip().removesuffix(")")
    try:
        return ast.literal_eval(ast.parse(f"dict({content})", mode="eval"))
    except (SyntaxError, ValueError):
        result = {}
        for item in re.split(r",\s*(?=[A-Za-z_]\w*=)", content):
            key, separator, value = item.partition("=")
            if not separator:
                continue
            try:
                result[key.strip()] = ast.literal_eval(value.strip())
            except (SyntaxError, ValueError):
                result[key.strip()] = value.strip()
        return result


def parse_evolution_log(
    path: Path, root: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    text = path.read_text(encoding="utf-8", errors="replace")
    metadata = run_metadata(path, root)
    compiler = CONFIG_COMPILERS.get(metadata["method"])
    baseline = None
    measurements = []

    rows = []
    evaluation_time = np.nan
    reproduction_time = np.nan
    for line_number, line in enumerate(text.splitlines(), 1):
        baseline_match = re.fullmatch(
            rf"Measure without transformations:\s*({FLOAT})", line.strip()
        )
        if baseline_match:
            baseline = abs(float(baseline_match.group(1)))
            measurements.append((baseline, line_number))
            continue
        if re.fullmatch(r"Gen\s+\d+", line.strip()):
            evaluation_time = np.nan
            reproduction_time = np.nan
            continue
        match = re.search(rf"Evaluation time:\s*({FLOAT})", line)
        if match:
            evaluation_time = float(match.group(1))
            continue
        match = re.search(rf"Reproduction time:\s*({FLOAT})", line)
        if match:
            reproduction_time = float(match.group(1))
            continue
        match = re.search(
            rf"Fitness on generation\s+(\d+):\s*({FLOAT})\s*"
            rf"\(({FLOAT})x speedup\)",
            line,
        )
        if match:
            fitness_seconds = abs(float(match.group(2)))
            measurements.append((fitness_seconds, line_number))
            rows.append(
                {
                    **metadata,
                    "generation": int(match.group(1)),
                    "fitness_seconds": fitness_seconds,
                    "speedup": float(match.group(3)),
                    "evaluation_seconds": evaluation_time,
                    "reproduction_seconds": reproduction_time,
                }
            )
    if compiler is None or baseline is None or not measurements:
        run = frame([], EVOLUTION_RUN_COLUMNS)
    else:
        seconds, fastest_line = min(measurements, key=lambda item: item[0])
        run = frame(
            [
                {
                    "benchmark": metadata["benchmark"],
                    "compiler": compiler,
                    "base": baseline,
                    "seconds": seconds,
                    "source": metadata["source"],
                    "line": fastest_line,
                }
            ],
            EVOLUTION_RUN_COLUMNS,
        )
    return run, frame(rows, GENERATION_COLUMNS)


def parse_mcts_jsonl(
    path: Path, root: Path
) -> pd.DataFrame:
    metadata = run_metadata(path, root)
    records = []
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "speedup" not in record:
                continue
            records.append(
                {
                    **metadata,
                    "line": line_number,
                    "timestamp": record.get("timestamp", ""),
                    "rollouts": record.get("cnt_rollouts", pd.NA),
                    "evaluations": record.get("cnt_evals", pd.NA),
                    "speedup": record["speedup"],
                    "transform": json.dumps(record.get("transform", [])),
                }
            )
    progress = frame(records, MCTS_PROGRESS_COLUMNS)
    return progress


def parse_mcts_stdout(path: Path, root: Path) -> pd.DataFrame:
    metadata = run_metadata(path, root)
    compiler = CONFIG_COMPILERS.get(metadata["method"])
    if compiler is None:
        return frame([], MCTS_RUN_COLUMNS)

    initial_time = None
    rows = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
    ):
        match = re.fullmatch(
            rf"(initial|optimized) time:\s*({FLOAT})", line.strip()
        )
        if not match:
            continue
        kind = match.group(1)
        seconds = float(match.group(2))
        if np.isfinite(seconds) and seconds > 0:
            if kind == "initial" and initial_time is None:
                initial_time = seconds
            rows.append(
                {
                    "benchmark": metadata["benchmark"],
                    "compiler": compiler,
                    "base": np.nan,
                    "seconds": seconds,
                    "source": metadata["source"],
                    "line": line_number,
                }
            )
    if not rows or initial_time is None:
        return frame([], MCTS_RUN_COLUMNS)
    measurements = frame(rows, MCTS_RUN_COLUMNS)
    fastest = measurements.loc[
        [measurements["seconds"].idxmin()]
    ].reset_index(drop=True)
    fastest["base"] = initial_time
    return fastest[MCTS_RUN_COLUMNS]


def parse_poc_stdout(path: Path, root: Path) -> pd.DataFrame:
    metadata = run_metadata(path, root)
    compiler = CONFIG_COMPILERS.get(metadata["method"])
    if compiler is None:
        return frame([], POC_RUN_COLUMNS)

    baseline = None
    measurements = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
    ):
        baseline_match = re.fullmatch(
            rf"Baseline measure:\s*({FLOAT})", line.strip()
        )
        if baseline_match:
            baseline = float(baseline_match.group(1))
            measurements.append((baseline, line_number))
            continue
        measurement_match = re.fullmatch(
            rf"[^:]+:\s*({FLOAT})", line.strip()
        )
        if measurement_match:
            seconds = float(measurement_match.group(1))
            if np.isfinite(seconds) and seconds > 0:
                measurements.append((seconds, line_number))

    if baseline is None or not measurements:
        return frame([], POC_RUN_COLUMNS)
    seconds, fastest_line = min(measurements, key=lambda item: item[0])
    return frame(
        [
            {
                "benchmark": metadata["benchmark"],
                "compiler": compiler,
                "base": baseline,
                "seconds": seconds,
                "source": metadata["source"],
                "line": fastest_line,
            }
        ],
        POC_RUN_COLUMNS,
    )


def parse_pluto_files(
    paths: Iterable[Path], root: Path
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for path in paths:
        lines = pd.Series(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            dtype="string",
        )
        fields = lines.str.extract(
            rf"^(?P<executable>[^:]+):::(?P<repetition>\d+):::(?P<seconds>{FLOAT})$"
        ).dropna()
        if fields.empty:
            continue
        fields["repetition"] = pd.to_numeric(fields["repetition"])
        fields["seconds"] = pd.to_numeric(fields["seconds"])
        for line_index, record in fields.iterrows():
            name = EXECUTABLE_NAME.match(record["executable"])
            if not name:
                continue
            rows.append(
                {
                    "benchmark": name["benchmark"],
                    "compiler": name["compiler"],
                    "transformed": bool(name["transformed"]),
                    "repetition": record["repetition"],
                    "seconds": record["seconds"],
                    "source": str(path.relative_to(root)),
                    "line": line_index + 1,
                }
            )
    measurements = pd.DataFrame.from_records(rows)
    if measurements.empty:
        empty = frame([], PLUTO_RUN_COLUMNS)
        return empty.copy(), empty.copy()

    fastest = measurements.loc[
        measurements.groupby(
            ["benchmark", "compiler", "transformed"]
        )["seconds"].idxmin()
    ]
    plutor_runs = (
        fastest[fastest["transformed"]]
        .drop(columns=["transformed", "repetition"])
        .sort_values(["benchmark", "compiler"])
        .reset_index(drop=True)
    )
    original_runs = (
        fastest[~fastest["transformed"]]
        .drop(columns=["transformed", "repetition"])
        .sort_values(["benchmark", "compiler"])
        .reset_index(drop=True)
    )
    return (
        plutor_runs[PLUTO_RUN_COLUMNS],
        original_runs[PLUTO_RUN_COLUMNS],
    )


def concat(frames: list[pd.DataFrame], columns: list[str]) -> pd.DataFrame:
    nonempty = [item for item in frames if not item.empty]
    if not nonempty:
        return frame([], columns)
    return pd.concat(nonempty, ignore_index=True)[columns]


def fastest_by_benchmark(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return data
    indices = data.groupby(["benchmark", "compiler"])["seconds"].idxmin()
    return (
        data.loc[indices]
        .sort_values(["benchmark", "compiler"])
        .reset_index(drop=True)
    )


def collect(root: Path, output: Path) -> dict[str, pd.DataFrame]:
    evolution_pairs = [
        parse_evolution_log(path, root) for path in sorted(root.rglob("*.out.1.0"))
    ]
    mcts_progress = [
        parse_mcts_jsonl(path, root) for path in sorted(root.rglob("*.jsonl"))
    ]
    mcts_runs = [
        parse_mcts_stdout(path, root)
        for path in sorted(root.glob("mcts/**/*.stdout"))
    ]
    poc_runs = [
        parse_poc_stdout(path, root)
        for path in sorted(root.glob("poc/**/*.stdout"))
    ]
    plutor_runs, original_runs = parse_pluto_files(
        sorted(root.rglob("*.out")), root
    )
    tables = {
        "evolution_runs": fastest_by_benchmark(
            concat(
                [run for run, _ in evolution_pairs],
                EVOLUTION_RUN_COLUMNS,
            )
        ),
        "evolution_generations": concat(
            [generations for _, generations in evolution_pairs], GENERATION_COLUMNS
        ),
        "mcts_runs": fastest_by_benchmark(
            concat(mcts_runs, MCTS_RUN_COLUMNS)
        ),
        "poc_runs": fastest_by_benchmark(concat(poc_runs, POC_RUN_COLUMNS)),
        "mcts_progress": concat(mcts_progress, MCTS_PROGRESS_COLUMNS),
        "plutor_runs": plutor_runs,
        "original_runs": original_runs,
    }

    output.mkdir(parents=True, exist_ok=True)
    for stale_name in ("jobs.csv", "pluto_runs.csv"):
        stale_path = output / stale_name
        if stale_path.exists():
            stale_path.unlink()
    for name, table in tables.items():
        table.to_csv(output / f"{name}.csv", index=False)

    for name, table in tables.items():
        print(f"{name.replace('_', ' ')}: {len(table)}")
    print(f"CSV output: {output}")
    return tables


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=script_dir,
        help="root data directory (default: directory containing this script)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=script_dir / "analysis",
        help="directory for normalized CSV files",
    )
    args = parser.parse_args()
    collect(args.root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
