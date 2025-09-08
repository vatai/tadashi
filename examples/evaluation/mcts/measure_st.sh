#!/bin/bash

# USAGE: sbatch measure_st.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 20:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
source "${REPO_ROOT}/scripts/genoa.source"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
NUM_REPS=10
SIZE=EXTRALARGE
OFLAG=3
export OMP_NUM_THREADS=1

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
	grep -v polybench/utilities |
	grep -v TMPFILE |
	grep -v INFIX |
	grep -v orig.c |
	grep -v pluto.c |
	tr "\n" "\0")

echo "OMP_NUM_THREADS=$OMP_NUM_THREADS"
for file in "${BENCHMARKS[@]}"; do
	benchmark="$(basename "${file%.c}")"
	srun -Q -n 1 python3 ./mcts_polybench.py "${benchmark}" --rollouts=5000 --prefix=data-st "$@" &
done
wait
echo "done"
