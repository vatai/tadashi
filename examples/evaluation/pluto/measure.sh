#!/bin/bash

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
NUM_REPS=10
SIZE=EXTRALARGE
OFLAG=3
OUTFILE="pluto_times_${SIZE}_O${OFLAG}_${NUM_REPS}.csv"

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name *."pluto.${SIZE}_O${OFLAG}.x" |
                                   tr "\n" "\0")
rm "$OUTFILE"
for file in "${BENCHMARKS[@]}"; do
    echo "$file"
    echo -n -e "$(basename "${file%.pluto.${SIZE}_O${OFLAG}.x}")\t" >> "$OUTFILE"
    for _ in $(seq "$NUM_REPS"); do
        $file | tr "\n" "\t" >> "$OUTFILE"
    done
    echo "" >> "$OUTFILE"
done

echo "done"
