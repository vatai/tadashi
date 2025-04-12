#!/bin/bash
#SBATCH --job-name=TADASHI       # create a short name for your job
#SBATCH --nodes=1                # node count
#SBATCH --time=24:00:00          # total run time limit (HH:MM:SS)
#SBATCH --mail-type=begin        # send email when job begins
#SBATCH --mail-type=end          # send email when job ends
#SBATCH --mail-user=alexander.drozd@gmail.com

# ======== Modules ========
#source /etc/profile.d/modules.sh
#source modules.sh

module load system/genoa mpi/mpich-x86_64
. ../../../scripts/genoa/source


PYTHONPATH=../../../ python3 🌳.py
