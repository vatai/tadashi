#!/usr/bin/bash

# USAGE: sbatch genova.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -J poc_all
#SBATCH -t 20:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt

### SET UP ENV ###
REPO_ROOT="$(git rev-parse --show-toplevel)"
source "${REPO_ROOT}/scripts/genoa.source"

### RUN COMMAND ###
python3 all.py "$@"
