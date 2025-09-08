#!/usr/bin/bash

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
	grep -v polybench/utilities |
	grep -v TMPFILE |
	grep -v INFIX |
	grep -v orig.c |
	grep -v pluto.c |
	tr "\n" "\0")

for benchmark in "${BENCHMARKS[@]}"; do
    name="$(basename "${benchmark%*.c}")"
    sbatch --exclude=genoa12 -J "${name}" measure_mt.sh
done
