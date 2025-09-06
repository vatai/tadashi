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
OUTFILE="pluto_times_${SIZE}_O${OFLAG}_${NUM_REPS}_NT${OMP_NUM_THREADS}-${SLURM_JOB_ID}.csv"

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name *."pluto.${SIZE}_O${OFLAG}.x" |
                                   tr "\n" "\0")
rm "$OUTFILE"
for file in "${BENCHMARKS[@]}"; do
    echo "$file"
    for rep in $(seq "$NUM_REPS"); do
        echo "$(basename "${file%.pluto."${SIZE}_O${OFLAG}".x}") $rep $(srun -n 1 "$file")"
    done
done

echo "done"
