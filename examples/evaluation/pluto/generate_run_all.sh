#!/bin/bash

# set -x

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
NUM_REPS=10
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

mkdir restuls

for file in "${BENCHMARKS[@]}"; do
	pjsub -j -o "results/$(basename ${file%.c})" \
		-x NUM_REPS \
		-x file \
		-x SIZE \
		-x OFLAG \
		<<'PJSUB_EOF'
echo "$OMP_NUM_THREADS"
basename "$file"
for CC in gcc fcc clang-19 clang-21; do

        pluto_bin="${file%.c}.pluto.${SIZE}_O${OFLAG}.${CC}.x"
        bin="${file%.c}.${SIZE}_O${OFLAG}.${CC}.x"
        for rep in $(seq "$NUM_REPS"); do
                echo "$(basename "${file%.pluto."${SIZE}_O${OFLAG}".x}"):::$rep:::$("$bin")"
        done
        for rep in $(seq "$NUM_REPS"); do
                echo "$(basename "${file%.pluto."${SIZE}_O${OFLAG}".x}"):::$rep:::$("$pluto_bin")"
        done
done
PJSUB_EOF
done

echo "done"
