#!/usr/bin/bash
#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 1

source ./scripts/genoa/source
python -m tadashi.mcts
