#!/usr/bin/bash

# USAGE: sbatch genoa.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -n 192
#SBATCH -t 5:00:00
#SBATCH -o pluto-st-%x-%j.txt
#SBATCH -e pluto-st-%x-%j.txt

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
NUM_REPS=10
SIZE=EXTRALARGE
OFLAG=3
export OMP_NUM_THREADS=1

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name *."pluto.${SIZE}_O${OFLAG}.x" |
                                   tr "\n" "\0")
for file in "${BENCHMARKS[@]}"; do
    # echo "$file"
    for rep in $(seq "$NUM_REPS"); do
        echo "$(basename "${file%.pluto."${SIZE}_O${OFLAG}".x}"):::$rep:::$(srun -Q -n 1 "$file")" &
    done
done
wait

echo "done"
