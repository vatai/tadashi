#!/usr/bin/bash

set -e
set -x

source "$(dirname $0)/common.sh"
CMD="$GIT_ROOT/build/tadashi --no-legality-check -d tadashi.isl_union_map -s tadashi.yaml"
POLYROOT=$GIT_ROOT/deps/downloads/polybench-c-3.2
POLYFILES="$(find $POLYROOT -mindepth 3 -name '*.c')"
for BENCHMARK_FILE in ${POLYFILES}; do
    export C_INCLUDE_PATH="${POLYROOT}/utilities"
    $CMD $BENCHMARK_FILE
done
