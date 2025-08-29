#!/usr/bin/bash

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 10:00:00
# #SBATCH -n 1
# #SBATCH -c 1

REPO_ROOT="$(git rev-parse --show-toplevel)"
source "${REPO_ROOT}/deps/set_env.src"
set_env "${REPO_ROOT}/deps/opt"

PYTHONPATH="${REPO_ROOT}" python3 "${REPO_ROOT}/examples/evaluation/evol_tadashi.py"
