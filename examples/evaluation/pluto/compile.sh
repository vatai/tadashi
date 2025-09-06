#!/usr/bin/bash

# USAGE: sbatch compile.sh

#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 5:00:00
#SBATCH -o %x-%j.txt
#SBATCH -e %x-%j.txt

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
PLUTO=${PLUTO:-$REPO_ROOT/deps/build/pluto-0.13.0/polycc}
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
SIZE=EXTRALARGE
OFLAG=3

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
                                   grep -v polybench/utilities |
                                   grep -v TMPFILE |
                                   grep -v INFIX |
                                   grep -v pluto.c |
                                   tr "\n" "\0")
GCC_ARGS=(
    "${POLYBENCH_ROOT}/utilities/polybench.c"
    "-I${POLYBENCH_ROOT}/utilities"
    "-DPOLYBENCH_TIME"
    "-DPOLYBENCH_USE_RESTRICT"
    "-D${SIZE}_DATASET"
    "-O${OFLAG}"
    "-lm"
    "-fopenmp"
)

for file in "${BENCHMARKS[@]}"; do
    cd "$(dirname "$file")" || exit
    test -f "${file%.c}.pluto.c" || $PLUTO "$file"
    gcc -o "${file%.c}.pluto.${SIZE}_O${OFLAG}.x" "${file%.c}.pluto.c" "${GCC_ARGS[@]}"
    cd - > /dev/null || exit
done

echo "done"
