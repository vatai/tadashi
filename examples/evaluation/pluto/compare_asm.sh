#!/usr/bin/bash
# Compare two polybench sources: pragmas first, then the compiled
# kernels (assembly) as confirmation.
# USAGE: compare_asm.sh <a.c> <b.c>
# Exit 0 if pragmas and normalized disassemblies match, 1 otherwise.
set -e

A="$1"
B="$2"
SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
REPO_ROOT="$(realpath "$SCRIPT_DIR/../../..")"
POLYBENCH_ROOT="$REPO_ROOT/examples/polybench"
SIZE=${SIZE:-EXTRALARGE}
OFLAG=${OFLAG:-3}
GCC_ARGS=(
	"-I${POLYBENCH_ROOT}/utilities"
	"-I$(dirname "$(realpath "$A")")"
	"-I$(dirname "$(realpath "$B")")"
	"-DPOLYBENCH_TIME"
	"-DPOLYBENCH_USE_RESTRICT"
	"-D${SIZE}_DATASET"
	"-O${OFLAG}"
	"-fopenmp"
	"-c"
)

disasm() {
	local src="$1" obj="$2"
	gcc "${GCC_ARGS[@]}" "$src" -o "$obj"
	objdump -d --no-show-raw-insn "$obj" |
		sed -e 's/^[0-9a-f]\+ <\([^>]*\)>:/<FUNC>:/' \
			-e 's/^\s*[0-9a-f]\+:\s*//' \
			-e 's/[0-9a-f]\+ <[^>]*>/<TARGET>/g' \
			-e '/^$/d' -e '/file format/d' -e '/Disassembly of section/d'
}

# Ordered pragma sequence; iterator names normalized to IT; the
# scop/endscop markers are harness delimiters, not generated code.
pragmas() {
	grep -E '^[[:space:]]*#pragma' "$1" |
		grep -v -E '#pragma (end)?scop' |
		sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]\+/ /g' \
			-e 's/\b_tadashi_[0-9]\+\b/IT/g' -e 's/\bt[0-9]\+\b/IT/g' ||
		true
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pragmas "$A" > "$WORK/a.pragmas"
pragmas "$B" > "$WORK/b.pragmas"
if ! diff "$WORK/a.pragmas" "$WORK/b.pragmas" > "$WORK/pragma_diff.txt"; then
	echo "DIFFERS (pragmas): $A vs $B"
	head -40 "$WORK/pragma_diff.txt"
	exit 1
fi

disasm "$A" "$WORK/a.o" > "$WORK/a.asm"
disasm "$B" "$WORK/b.o" > "$WORK/b.asm"

if diff "$WORK/a.asm" "$WORK/b.asm" > "$WORK/diff.txt"; then
	echo "IDENTICAL: $A vs $B"
else
	echo "DIFFERS: $A vs $B ($(wc -l < "$WORK/diff.txt") diff lines)"
	head -40 "$WORK/diff.txt"
	exit 1
fi
