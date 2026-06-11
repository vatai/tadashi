#!/usr/bin/bash

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
PLUTO=${PLUTO:-polycc}
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"

readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
	grep -v polybench/utilities |
	grep -v TMPFILE |
	grep -v INFIX |
	grep -v orig.c |
	grep -v pluto.c |
	tr "\n" "\0")

mkdir pluto
for file in "${BENCHMARKS[@]}"; do
	for NT in st mt; do
		for CC in gcc fcc clang-21; do
			BM=$(basename ${file%.*})
			pjsub -j -o "pluto/${NT}-pluto-${BM}-${CC}.%j" \
				-N "${NT}-pluto-${BM}-${CC}" \
				-x file=$file \
				-x NT=$NT \
				-x CC=$CC \
				fsub.sh
		done
	done
done
