#!/usr/bin/bash

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
	for NT in st mt; do
		BM=$(basename ${file%.*})
		pjsub -j -o evo/${BM}.%j \
			-N evo/$NT-evo-${BM} \
			-x ENTRYPOINT=evo.py \
			-x ROOT="$REPO_ROOT/../ML4TADASHI/scripts/$NT-evo" \
			-x BENCHMARK=$BM \
			fsub.sh
		pjsub -j -o mcts/$NT-mtcs-${BM}.%j \
			-N mcts/${BM} \
			-x ENTRYPOINT=mcts.py \
			-x ROOT="$REPO_ROOT/examples/evaluation/mcts/$NT-mcts" \
			-x BENCHMARK=$BM \
			fsub.sh
		pjsub -j -o poc/$NT-poc-${BM}.%j \
			-N poc-${BM} \
			-x ENTRYPOINT=poc.py \
			-x ROOT="$REPO_ROOT/examples/evaluation/poc/$NT-poc" \
			-x BENCHMARK=$BM \
			fsub.sh
	done
done
