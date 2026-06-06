#!/bin/bash

# USAGE: sbatch measure_mt.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 5:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt
#

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
NUM_REPS=10
SIZE=EXTRALARGE
OFLAG=3
# export OMP_NUM_THREADS=1

SRUN=()
if command -v srun >/dev/null 2>&1; then
    SRUN=(srun -Q -n 1)
fi

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name *."pluto.${SIZE}_O${OFLAG}.x" |
                                   tr "\n" "\0")

echo "$OMP_NUM_THREADS"
for file in "${BENCHMARKS[@]}"; do
    # echo "$file"
    for rep in $(seq "$NUM_REPS"); do
        echo "$(basename "${file%.pluto."${SIZE}_O${OFLAG}".x}"):::$rep:::$("${SRUN[@]}" "$file")"
    done
done

echo "done"
