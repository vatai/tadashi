#!/bin/bash

set -x

REPO_ROOT=$(git rev-parse --show-toplevel)
PLUTO=${PLUTO:-$REPO_ROOT/deps/build/pluto-0.13.0/polycc}
POLYBENCH_ROOT="$(readpath $1)"

find "$POLYBENCH_ROOT" -name '*.c' | grep -v polybench/utilities | while read -r file; do
    cd "$(dirname "$file")" || exit
    $PLUTO $file
    gcc -o "${file%.c}.pluto.x" "${file%.c}.pluto.c" "$1/utilities/polybench.c" -I "$1/utilities/polybench.c"
    cd - > /dev/null || exit
done

echo "done"
