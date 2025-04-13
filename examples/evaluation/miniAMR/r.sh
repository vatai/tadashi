#!/bin/bash
#SBATCH --job-name=TADASHI       # create a short name for your job
#SBATCH --nodes=1                # node count
#SBATCH --time=24:00:00          # total run time limit (HH:MM:SS)
#SBATCH --mail-type=begin        # send email when job begins
#SBATCH --mail-type=end          # send email when job ends

source ../../../scripts/genoa/source

PYTHONPATH=../../../ python3 🌳.py
