#!/bin/bash
#SBATCH --job-name=TADASHI       # create a short name for your job
#SBATCH --nodes=1                # node count
#SBATCH --time=24:00:00          # total run time limit (HH:MM:SS)

source ../../../scripts/genoa/source

PYTHONPATH=../../../ python3 🌳.py
