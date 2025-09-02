#!/usr/bin/bash

# USAGE: sbatch genoa.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 5:00:00
#SBATCH -o pluto-%x-%j.txt
#SBATCH -e pluto-%x-%j.txt

./compile.sh
./measure.sh

