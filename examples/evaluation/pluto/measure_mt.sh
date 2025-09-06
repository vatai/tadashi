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

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name *."pluto.${SIZE}_O${OFLAG}.x" |
                                   tr "\n" "\0")
hostname
test $(hostname) == genoa12.cloud.r-ccs.riken.jp && exit
echo "$OMP_NUM_THREADS"
for file in "${BENCHMARKS[@]}"; do
    # echo "$file"
    for rep in $(seq "$NUM_REPS"); do
        echo "$(basename "${file%.pluto."${SIZE}_O${OFLAG}".x}"):::$rep:::$(srun -Q -n 1 "$file")"
    done
done

echo "done"
