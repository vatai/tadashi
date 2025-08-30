#!/usr/bin/bash

# Usage sbatch -J benchmark evol_tadashi.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 10:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt


### SET UP ENV ###
module load mpi/mpich-x86_64

REPO_ROOT="$(git rev-parse --show-toplevel)"
source "${REPO_ROOT}/deps/set_env.src"
set_env "${REPO_ROOT}/deps/opt"
EVOL_TADASHI_PY="${REPO_ROOT}/examples/evaluation/evol_tadashi.py"
export PYTHONPATH="${REPO_ROOT}"


### RUN COMMAND ###
python3 "${EVOL_TADASHI_PY}" --benchmark="${SLURM_JOB_NAME}" "$@"
