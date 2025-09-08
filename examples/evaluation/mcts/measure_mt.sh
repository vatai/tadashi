#!/bin/bash

# USAGE: sbatch measure_mt.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 20:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt

### SET UP ENV ###
REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
source "${REPO_ROOT}/scripts/genoa.source"

echo "OMP_NUM_THREADS=$OMP_NUM_THREADS"
python3 ./mcts_polybench.py "${SLURM_JOB_NAME}" --rollouts=5000 --prefix=data-mt --allow-omp "$@"

