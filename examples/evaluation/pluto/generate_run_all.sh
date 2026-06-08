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

mkdir results

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
