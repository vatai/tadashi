#!/bin/bash

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
PLUTO=${PLUTO:-$REPO_ROOT/deps/build/pluto-0.13.0/polycc}
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
                                   grep -v polybench/utilities |
                                   grep -v pluto.c |
                                   tr "\n" "\0")
GCC_ARGS=(
    "${POLYBENCH_ROOT}/utilities/polybench.c"
    "-I${POLYBENCH_ROOT}/utilities"
    "-DPOLYBENCH_TIME"
    "-DPOLYBENCH_USE_RESTRICT"
    "-lm"
    "-fopenmp"
)

for file in "${BENCHMARKS[@]}"; do
    cd "$(dirname "$file")" || exit
    test -f "${file%.c}.pluto.c" || $PLUTO "$file"
    test -f "${file%.c}.pluto.x" || gcc -o "${file%.c}.pluto.x" "${file%.c}.pluto.c" "${GCC_ARGS[@]}"
    cd - > /dev/null || exit
done

echo "done"
