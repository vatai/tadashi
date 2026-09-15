#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from collect_results import (
    collect,
    parse_evolution_log,
    parse_mcts_jsonl,
    parse_mcts_stdout,
    parse_poc_stdout,
    parse_pluto_files,
)
from report_results import (
    build_abs_speedup,
    build_merged,
    evolution_speedups,
    geometric_mean,
    mcts_speedups,
    poc_speedups,
    pluto_speedups,
)


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def make_run_file(self, suffix, content):
        path = (
            self.root
            / "experiment"
            / "EXTRALARGE"
            / "config"
            / "pet"
            / "gemm-seed42"
            / suffix
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_evolution_log_returns_dataframes(self):
        path = self.make_run_file(
            "pjsub.1.out.1.0",
            """ml_args=Namespace(init_seed=42, population_size=200, max_gen=10)
app_args=Namespace(translator='Pet', benchmark='gemm', dataset='EXTRALARGE')
Measure without transformations: -10.0
Gen 0
Evaluation time: 2.5
Reproduction time: 1.5
  Fitness on generation 0: -5.0 (2.000x speedup)
Final model: [[0, 1, tadashi.TrEnum.INTERCHANGE, ]] --- -5.0
""",
        )
        run, generations = parse_evolution_log(path, self.root)
        self.assertIsInstance(run, pd.DataFrame)
        self.assertEqual(run.loc[0, "benchmark"], "gemm")
        self.assertEqual(run.loc[0, "compiler"], "gcc")
        self.assertEqual(run.loc[0, "base"], 10.0)
        self.assertEqual(run.loc[0, "seconds"], 5.0)
        self.assertEqual(run.loc[0, "line"], 7)
        self.assertEqual(generations.loc[0, "evaluation_seconds"], 2.5)

    def test_mcts_jsonl_returns_progress_dataframe(self):
        path = self.make_run_file(
            "gemm.jsonl",
            """{"cnt_rollouts": 0, "cnt_evals": 0, "speedup": 1}
{"cnt_rollouts": 3, "cnt_evals": 5, "speedup": 4, "transform": [[1, "tile_1d", 32]]}
""",
        )
        progress = parse_mcts_jsonl(path, self.root)
        self.assertEqual(progress.loc[1, "speedup"], 4)
        self.assertEqual(progress.loc[1, "evaluations"], 5)
        self.assertEqual(len(progress), 2)

    def test_mcts_stdout_uses_fastest_absolute_runtime(self):
        path = (
            self.root
            / "mcts"
            / "EXTRALARGE"
            / "ro10000"
            / "pet-fcc"
            / "gemm-seed42"
            / "pjsub.1.stdout"
        )
        path.parent.mkdir(parents=True)
        path.write_text(
            "initial time: 10.0\n"
            "optimized time: 8.0\n"
            "speedup: 1.25\n"
            "optimized time: 2.0\n"
            "speedup: 5.0\n",
            encoding="utf-8",
        )
        run = parse_mcts_stdout(path, self.root)
        self.assertEqual(
            list(run.columns),
            ["benchmark", "compiler", "base", "seconds", "source", "line"],
        )
        self.assertEqual(run.loc[0, "compiler"], "fcc")
        self.assertEqual(run.loc[0, "base"], 10.0)
        self.assertEqual(run.loc[0, "seconds"], 2.0)
        self.assertEqual(run.loc[0, "line"], 4)

    def test_mcts_speedup_uses_measured_base(self):
        mcts = pd.DataFrame(
            [
                {
                    "benchmark": "gemm",
                    "compiler": "gcc",
                    "base": 8.0,
                    "seconds": 2.0,
                }
            ]
        )
        result = mcts_speedups(mcts)
        self.assertEqual(result.loc[0, "method"], "mcts-gcc")
        self.assertEqual(result.loc[0, "speedup"], 4.0)

    def test_poc_stdout_and_speedup(self):
        path = (
            self.root
            / "poc"
            / "poc-runs"
            / "EXTRALARGE"
            / "pet"
            / "gemm"
            / "pjsub.1.stdout"
        )
        path.parent.mkdir(parents=True)
        path.write_text(
            "Baseline measure: 10.0\n"
            "Tiling with size 20 ...\n"
            "Tiling with size 20: 2.0\n",
            encoding="utf-8",
        )
        run = parse_poc_stdout(path, self.root)
        self.assertEqual(run.loc[0, "base"], 10.0)
        self.assertEqual(run.loc[0, "seconds"], 2.0)
        result = poc_speedups(run)
        self.assertEqual(result.loc[0, "method"], "poc-gcc")
        self.assertEqual(result.loc[0, "speedup"], 5.0)

    def test_pluto_output_and_speedup(self):
        path = self.root / "pluto" / "results" / "gemm.out"
        path.parent.mkdir(parents=True)
        path.write_text(
            "gemm.EXTRALARGE_O3.gcc.x:::1:::10.0\n"
            "gemm.EXTRALARGE_O3.gcc.x:::2:::11.0\n"
            "gemm.pluto.EXTRALARGE_O3.gcc.x:::1:::2.0\n",
            encoding="utf-8",
        )
        plutor_runs, original_runs = parse_pluto_files([path], self.root)
        speedups = pluto_speedups(plutor_runs, original_runs)
        self.assertEqual(len(plutor_runs), 1)
        self.assertEqual(len(original_runs), 1)
        self.assertEqual(original_runs.loc[0, "seconds"], 10.0)
        self.assertNotIn("transformed", plutor_runs.columns)
        self.assertNotIn("repetition", plutor_runs.columns)
        self.assertEqual(speedups.loc[0, "speedup"], 5.0)

    def test_report_keeps_experiments_separate(self):
        runs = pd.DataFrame(
            [
                {
                    "benchmark": "gemm",
                    "compiler": "gcc",
                    "base": 10.0,
                    "seconds": 2.0,
                },
            ]
        )
        results = evolution_speedups(runs)
        self.assertEqual(results.loc[0, "method"], "evolution-gcc")
        self.assertEqual(results.loc[0, "speedup"], 5.0)

    def test_geometric_mean_uses_numpy(self):
        self.assertAlmostEqual(geometric_mean(pd.Series([1.0, 4.0])), 2.0)
        self.assertAlmostEqual(
            geometric_mean(pd.Series([1.0, np.nan, 9.0])), 3.0
        )

    def test_merged_runtime_table(self):
        input_dir = self.root / "analysis"
        input_dir.mkdir()
        pd.DataFrame(
            [{"benchmark": "gemm", "compiler": "gcc", "seconds": 10.0}]
        ).to_csv(input_dir / "original_runs.csv", index=False)
        pd.DataFrame(
            [{"benchmark": "gemm", "compiler": "gcc", "seconds": 2.0}]
        ).to_csv(input_dir / "plutor_runs.csv", index=False)
        pd.DataFrame(
            [
                {
                    "benchmark": "gemm",
                    "compiler": "gcc",
                    "base": 8.0,
                    "seconds": 4.0,
                }
            ]
        ).to_csv(input_dir / "mcts_runs.csv", index=False)
        pd.DataFrame(
            [
                {
                    "benchmark": "gemm",
                    "compiler": "gcc",
                    "base": 10.0,
                    "seconds": 5.0,
                }
            ]
        ).to_csv(input_dir / "poc_runs.csv", index=False)
        pd.DataFrame(
            [
                {
                    "benchmark": "gemm",
                    "compiler": "gcc",
                    "base": 9.0,
                    "seconds": 3.0,
                }
            ]
        ).to_csv(input_dir / "evolution_runs.csv", index=False)

        merged = build_merged(input_dir)
        self.assertEqual(merged.loc[0, "orignial-time"], 10.0)
        self.assertEqual(merged.loc[0, "pluto-speedup"], 5.0)
        self.assertEqual(merged.loc[0, "mcts-speedup"], 2.0)
        self.assertEqual(
            merged.loc[0, "mcts-speedup-to-original"], 2.5
        )
        self.assertEqual(merged.loc[0, "poc-speedup"], 2.0)
        self.assertEqual(
            merged.loc[0, "poc-speedup-to-original"], 2.0
        )
        self.assertEqual(merged.loc[0, "evo-speedup"], 3.0)
        self.assertAlmostEqual(
            merged.loc[0, "evo-speedup-to-original"], 10.0 / 3.0
        )

    def test_absolute_speedup_uses_fastest_compilers(self):
        input_dir = self.root / "analysis"
        input_dir.mkdir()
        pd.DataFrame(
            [
                {"benchmark": "gemm", "compiler": "gcc", "seconds": 10.0},
                {"benchmark": "gemm", "compiler": "fcc", "seconds": 8.0},
            ]
        ).to_csv(input_dir / "original_runs.csv", index=False)
        for name, seconds in [
            ("plutor_runs", [4.0, 2.0]),
            ("poc_runs", [5.0, 3.0]),
            ("mcts_runs", [6.0, 4.0]),
            ("evolution_runs", [7.0, 1.0]),
        ]:
            pd.DataFrame(
                [
                    {
                        "benchmark": "gemm",
                        "compiler": compiler,
                        "seconds": runtime,
                    }
                    for compiler, runtime in zip(("gcc", "fcc"), seconds)
                ]
            ).to_csv(input_dir / f"{name}.csv", index=False)

        result = build_abs_speedup(input_dir)
        self.assertEqual(result.loc[0, "original-time"], 8.0)
        self.assertEqual(result.loc[0, "pluto-speedup"], 4.0)
        self.assertAlmostEqual(result.loc[0, "poc-speedup"], 8.0 / 3.0)
        self.assertEqual(result.loc[0, "mcts-speedup"], 2.0)
        self.assertEqual(result.loc[0, "evo-speedup"], 8.0)

    def test_collection_ignores_stat_files_and_removes_stale_jobs_csv(self):
        self.make_run_file(
            "pjsub.1.out.1.0",
            """Measure without transformations: -10.0
Final model: [] --- -5.0
""",
        )
        self.make_run_file("pjsub.1.stat", "JOB ID : 1\n")
        output = self.root / "analysis"
        output.mkdir()
        (output / "jobs.csv").write_text("stale\n", encoding="utf-8")
        (output / "pluto_runs.csv").write_text("stale\n", encoding="utf-8")
        tables = collect(self.root, output)
        self.assertNotIn("jobs", tables)
        self.assertFalse((output / "jobs.csv").exists())
        self.assertNotIn("pluto_runs", tables)
        self.assertFalse((output / "pluto_runs.csv").exists())


if __name__ == "__main__":
    unittest.main()
