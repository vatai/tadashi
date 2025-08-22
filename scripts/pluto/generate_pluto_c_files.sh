#!/bin/bash

# set -x

PLUTO=./deps/build/pluto-0.13.0/polycc

find "$(realpath "$1")" -name '*.c' | grep -v polybench/utilities | while read -r file; do
    cd "$(dirname "$file")" || exit
    $PLUTO $file
    gcc -o "${file%.c}.pluto.x" "${file%.c}.pluto.c" "$1/utilities/polybench.c" -I "$1/utilities/polybench.c"
    cd - > /dev/null || exit
done

echo "done"
