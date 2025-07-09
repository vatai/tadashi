#!/usr/bin/bash
set -x

# salloc -N 2 -p genoa -t 10:00

function set_env ()
{
  echo "$1"
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

module load system/genoa mpi/mpich-x86_64
set_env /home/users/emil.vatai/code/tadashi/deps/opt
source /home/users/emil.vatai/code/tadashi/venv/bin/activate

HOSTS_FILE=/tmp/hosts-$SLURM_JOB_ID.txt
srun hostname > "$HOSTS_FILE"

while read -r HOST; do
  if [ "$HOST" == "$(hostname)" ]; then
    ssh -n "$HOST" "
function set_env ()
{
  echo "$1"
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

module load system/genoa mpi/mpich-x86_64
set_env /home/users/emil.vatai/code/tadashi/deps/opt
source /home/users/emil.vatai/code/tadashi/venv/bin/activate
    ray start --head --node-ip-address="$HOST" --num-cpus=0"
  else
    ssh -n "$HOST" hostname
    ssh -n "$HOST" "
function set_env ()
{
  echo "$1"
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

module load system/genoa mpi/mpich-x86_64
set_env /home/users/emil.vatai/code/tadashi/deps/opt
source /home/users/emil.vatai/code/tadashi/venv/bin/activate
    ray start --address="$(hostname):6379" --num-cpus=1"
  fi
done < "$HOSTS_FILE"

python first.py

rm "$HOSTS_FILE"
echo DONE!
