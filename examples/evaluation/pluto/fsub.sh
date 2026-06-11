#!/bin/bash

#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -L rscgrp=small
#PJM -L elapse=30:00
#PJM -L node=1
# #PJM --llio localtmp-size=40Gi

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
SIZE=EXTRALARGE
OFLAG=3

GCC_ARGS=(
	"${POLYBENCH_ROOT}/utilities/polybench.c"
	"-I${POLYBENCH_ROOT}/utilities"
	"-DPOLYBENCH_TIME"
	"-DPOLYBENCH_USE_RESTRICT"
	"-D${SIZE}_DATASET"
	"-O${OFLAG}"
	"-lm"
)

if [[ "$NT" == "mt" ]]; then
	GCC_ARGS+=("-fopenmp")
fi

module load LLVM/llvmorg-21.1.0

cd "$(dirname "$file")" || exit
test -f "${file%.c}.pluto.c" || $PLUTO "$file"
BINARY="${file%.c}.pluto.${SIZE}_O${OFLAG}.${CC}.${NT}.x"
$CC -o "$BINARY" "${file%.c}.pluto.c" "${GCC_ARGS[@]}"

echo "--- RUNS ---"
echo $BINARY
for r in $(seq 3); do
	"./$BINARY"
done

cd - >/dev/null || exit
