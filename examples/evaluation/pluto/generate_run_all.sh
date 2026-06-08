#!/bin/bash

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
NUM_REPS=3
SIZE=EXTRALARGE
OFLAG=3
# export OMP_NUM_THREADS=1

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
	grep -v polybench/utilities |
	grep -v TMPFILE |
	grep -v INFIX |
	grep -v orig.c |
	grep -v pluto.c |
	tr "\n" "\0")

mkdir -p results

for file in "${BENCHMARKS[@]}"; do
	name="$(basename ${file%.c})"
	pjsub -j \
		-o "results/${name}.%j.out" \
		-e "results/${name}.%j.err" \
		-N "pluto_${name}" \
		-x NUM_REPS="$NUM_REPS" \
		-x file="$file" \
		-x SIZE="$SIZE" \
		-x OFLAG="$OFLAG" \
		<<'PJSUB_EOF'
#!/bin/bash
#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -L elapse=5:00:00
#PJM -L node=1
OMP_NUM_THREADS=48
run_all() {
	for rep in $(seq "$NUM_REPS"); do
		echo "$(basename "$bin"):::$rep:::$("$bin")"
	done

	for rep in $(seq "$NUM_REPS"); do
		echo "$(basename "$pluto_bin"):::$rep:::$("$pluto_bin")"
	done
}


bin="${file%.c}.${SIZE}_O${OFLAG}.${CC}.x"
pluto_bin="${file%.c}.pluto.${SIZE}_O${OFLAG}.${CC}.x"
export CC=gcc
run_all

export CC=fcc
run_all

module load LLVM/llvmorg-21.1.0
export CC=clang-21
run_all
module unload LLVM/llvmorg-21.1.0

source /home/apps/oss/llvm-v19.1.4/init.sh
export CC=clang-19
run_all

PJSUB_EOF
done

echo "done"
