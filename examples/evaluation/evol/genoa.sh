#!/usr/bin/bash

# USAGE: sbatch -J ${benchmark} genoa.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 10:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt

### SET UP ENV ###
REPO_ROOT="$(git rev-parse --show-toplevel)"
source "${REPO_ROOT}/scripts/genoa.source"

### RUN COMMAND ###
python3 evol_gp.py --benchmark="${SLURM_JOB_NAME}" "$@"
