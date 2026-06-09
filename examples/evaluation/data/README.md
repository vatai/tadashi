# Evaluation Data Analysis

The analysis tools use pandas, NumPy, and matplotlib. They analyze benchmark
timings and search progress; `.stat` files and job-system data are ignored.

Run both collection and reporting from this directory:

```sh
make analyze
```

`collect_results.py` scans the extracted data recursively and writes normalized
CSV files to `analysis/`:

- `evolution_runs.csv`: initial baseline and fastest absolute evolution runtime
  per benchmark/compiler
- `evolution_generations.csv`: per-generation fitness and search time
- `mcts_runs.csv`: initial baseline and fastest absolute MCTS runtime from each
  stdout log
- `poc_runs.csv`: initial baseline and fastest absolute POC runtime from each
  stdout log
- `mcts_progress.csv`: complete MCTS progress histories
- `plutor_runs.csv`: fastest Pluto-transformed timing per benchmark/compiler
- `original_runs.csv`: fastest original timing per benchmark/compiler

`report_results.py` writes:

- `abs-speedup.csv`: fastest original and method walltimes across compilers,
  with absolute speedups
- `abs-speedup.{png,pdf}`: cross-compiler absolute speedup comparison
- `merged.csv`: original, Pluto, MCTS, and evolution runtimes and speedups
- `speedups.csv`: best speedup per method and benchmark
- `method_summary.csv`: benchmark counts, geometric means, medians, and maxima
- `benchmark_winners.csv`: best method for each benchmark
- `report.md`: Markdown summary
- `speedups.{png,pdf}`: per-benchmark speedup comparison
- `evolution_progress.{png,pdf}`: EvoTadashi progress by generation
- `mcts_progress.{png,pdf}`: MCTS progress by evaluation count

Both tools accept alternate paths:

```sh
python3 collect_results.py /path/to/data -o /tmp/evaluation-csv
python3 report_results.py /tmp/evaluation-csv -o /tmp/report.md
```

Run the parser tests with:

```sh
make test
```
