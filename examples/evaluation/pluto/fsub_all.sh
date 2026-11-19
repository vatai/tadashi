#!/usr/bin/bash

REPO_ROOT="$(realpath "$(git rev-parse --show-toplevel)")"
PLUTO=${PLUTO:-$REPO_ROOT/third_party/opt/bin/polycc}
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"

# adi is excluded: Clan cannot parse the (DATA_TYPE) casts in its scop, so Pluto
# never produces adi.pluto.c (see examples/evaluation/FAILURE-ANALYSIS.md).
readarray -d '' BENCHMARKS < <(find "$POLYBENCH_ROOT" -name '*.c' |
	grep -v polybench/utilities |
	grep -v TMPFILE |
	grep -v INFIX |
	grep -v orig.c |
	grep -v pluto.c |
	grep -v /adi/ |
	tr "\n" "\0")

mkdir -p st-pluto mt-pluto
for file in "${BENCHMARKS[@]}"; do
	for NT in st mt; do
		for CC in gcc fcc clang-21; do
			BM=$(basename ${file%.*})
			pjsub -j -o "${NT}-pluto/pluto-${BM}-${CC}.%j.out" \
				-N "${NT}-pluto-${BM}-${CC}" \
				-x file=$file \
				-x NT=$NT \
				-x CC=$CC \
				-x PLUTO=$PLUTO \
				fsub.sh
		done
	done
done
