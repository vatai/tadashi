#!/usr/bin/bash

# Pack the evaluation logs for analysis on a machine that has numpy/pandas/
# matplotlib (Fugaku has neither: the login node python3 lacks numpy and .venv is
# aarch64-only). Run this here, then "make data && make analyze" in
# examples/evaluation/data on that machine.

set -eu

EVALUATION_ROOT="$(realpath "$(dirname "$0")")"
ML4TADASHI_SCRIPTS="$(realpath "$EVALUATION_ROOT/../../../ML4TADASHI/scripts")"
DEST="${DEST:-$HOME}"

cd "$EVALUATION_ROOT"

# Measurement logs read by data/collect_results.py.
tar czf "$DEST/tadashi-results.tgz" \
	mcts/{st,mt}-mcts \
	pluto/{st,mt}-pluto \
	poc/{st,mt}-poc
tar czf "$DEST/ml4t-results.tgz" -C "$ML4TADASHI_SCRIPTS" st-evo mt-evo

# Correctness verdicts of the check sweep; these belong in data/check/ and are
# committed to the repo rather than fed to the analysis.
tar czf "$DEST/tadashi-check.tgz" -C data/check evo mcts poc

ls -lh "$DEST"/tadashi-results.tgz "$DEST"/ml4t-results.tgz "$DEST"/tadashi-check.tgz
