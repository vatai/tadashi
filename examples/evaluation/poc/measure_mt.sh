#!/bin/bash

# USAGE: sbatch measure_mt.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 20:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt
#SBATCH -n 192
# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
NUM_REPS=10
SIZE=EXTRALARGE
OFLAG=3
# export OMP_NUM_THREADS=1

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
                                   grep -v polybench/utilities |
                                   grep -v TMPFILE |
                                   grep -v INFIX |
                                   grep -v pluto.c |
                                   tr "\n" "\0")
hostname
test "x$(hostname)" == xgenoa12.cloud.r-ccs.riken.jp && exit
echo "OMP_NUM_THREADS=$OMP_NUM_THREADS"
for file in "${BENCHMARKS[@]}"; do
    # echo "$file"
    benchmark="$(basename "${file%.c}")"
    # echo "$(srun -Q -n 1 python3 ./all.py "${benchmark}")" &
    python3 ./all.py "${benchmark}" --allow-omp
done

echo "done"
