#!/bin/sh
set -e
set -x

if [ -e "$(which yum)" ]; then
	yum install -y gmp-c++ gmp-devel clang-devel-19.1.7 llvm-devel-19.1.7
elif [ -e "$(which apk)" ]; then
	apk add gmp-dev clang19-dev llvm19-dev
fi

ROOT="$(git rev-parse --show-toplevel)"
THIRD_PARTY="$ROOT/third_party"
ISL_ORIGIN="$THIRD_PARTY/isl.bundle"
PREFIX="$THIRD_PARTY/opt"
CLANG_PREFIX="$(dirname "$(dirname "$(realpath "$(which llvm-config-19)")")")"

cd "$THIRD_PARTY"
git clone https://repo.or.cz/isl.git
git clone https://repo.or.cz/pet.git

cd "$THIRD_PARTY/isl"
./autogen.sh
./configure --prefix="$PREFIX"
make -j install

cd "$THIRD_PARTY/pet"
./autogen.sh
./configure --prefix="$PREFIX" --with-clang-prefix="$CLANG_PREFIX" --with-isl-prefix="$PREFIX"
make -j install
