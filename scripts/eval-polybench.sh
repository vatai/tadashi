!/usr/bin/bash

source "$(dirname $0)/common.sh"
CMD="$GIT_ROOT/build/tadashi --no-legality-check -d tadashi.isl_union_map -s tadashi.yaml"
POLYROOT=$GIT_ROOT/deps/polybench-c-3.2
POLYFILES="$(find $POLYROOT -mindepth 3 -name '*.c')"
for BENCHMARK_FILE in ${POLYFILES}; do
    export C_INCLUDE_PATH="${POLYROOT}/utilities"
    SCHEDULE=$($CMD ${BENCHMARK_FILE} | grep Schedule: | cut -f2- -d\ )
    $CMD $BENCHMARK_FILE "$SCHEDULE"
done
