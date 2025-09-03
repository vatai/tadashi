#!/usr/bin/bash

# USAGE: sbatch genoa.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 10:00:00
#SBATCH -J overhead
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt

### SET UP ENV ###
REPO_ROOT="$(git rev-parse --show-toplevel)"
source "${REPO_ROOT}/scripts/genoa.source"

### RUN COMMAND ###
python3 rrl.py --verify
python3 rrl.py --num-steps=1
python3 rrl.py --num-steps=10
