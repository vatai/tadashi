#!/usr/bin/bash

#!/bin/bash
#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N tadashi_install
#PJM -L rscgrp=small
#PJM -L elapse=1:00:00
#PJM -L node=1
# #PJM --llio localtmp-size=40Gi
#PJM -j -S

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
PLUTO=${PLUTO:-$REPO_ROOT/deps/build/pluto-0.13.0/polycc}
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
SIZE=EXTRALARGE
OFLAG=3

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
	grep -v polybench/utilities |
	grep -v TMPFILE |
	grep -v INFIX |
	grep -v orig.c |
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

	export CC=gcc
	$CC -o "${file%.c}.pluto.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.pluto.c" "${GCC_ARGS[@]}"
	$CC -o "${file%.c}.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.c" "${GCC_ARGS[@]}"

	export CC=fcc
	$CC -o "${file%.c}.pluto.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.pluto.c" "${GCC_ARGS[@]}"
	$CC -o "${file%.c}.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.c" "${GCC_ARGS[@]}"

	module load LLVM/llvmorg-21.1.0
	export CC=clang-21
	$CC -o "${file%.c}.pluto.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.pluto.c" "${GCC_ARGS[@]}"
	$CC -o "${file%.c}.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.c" "${GCC_ARGS[@]}"
	module unload LLVM/llvmorg-21.1.0

	source /home/apps/oss/llvm-v19.1.4/init.sh
	export CC=clang-19
	$CC -o "${file%.c}.pluto.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.pluto.c" "${GCC_ARGS[@]}"
	$CC -o "${file%.c}.${SIZE}_O${OFLAG}.${CC}.x" "${file%.c}.c" "${GCC_ARGS[@]}"

	cd - >/dev/null || exit
done

echo "done"
