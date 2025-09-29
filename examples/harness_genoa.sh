#!/usr/bin/bash
#SBATCH -p genoa
#SBATCH -N 4
#SBATCH -n 4
#SBATCH -c 1

function set_env ()
{
  echo $1
  export PATH="$1/bin${PATH:+:${PATH}}"
  export PATH="$1/bin64${PATH:+:${PATH}}"
  export PATH="$1/libexec${PATH:+:${PATH}}"
  export LD_LIBRARY_PATH="$1/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  export LIBRARY_PATH="$1/lib${LIBRARY_PATH:+:${LIBRARY_PATH}}"
  export LD_LIBRARY_PATH="$1/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  export LIBRARY_PATH="$1/lib64${LIBRARY_PATH:+:${LIBRARY_PATH}}"
  export C_INCLUDE_PATH="$1/include${C_INCLUDE_PATH:+:${C_INCLUDE_PATH}}"
  export CPLUS_INCLUDE_PATH="$1/include${CPLUS_INCLUDE_PATH:+:${CPLUS_INCLUDE_PATH}}"
  export MAN_PATH="$1/man${MAN_PATH:+:${MAN_PATH}}"
}

module load system/genoa  mpi/mpich-x86_64
set_env /home/users/emil.vatai/code/tadashi/deps/opt
source /home/users/emil.vatai/code/tadashi/venv/bin/activate
# cmake --build build --clean-first
# CC=clang CXX=clang++ pip install pickle5
PYTHONPATH=.
export PYTHONPATH
mpirun -N 1 python ./examples/harness_demo.py
# -outfile-pattern ho.%r.out -errfile-pattern he.%r.err 
