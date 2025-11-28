#!/bin/sh
set -e
set -x

if [ -e "$(which yum)" ]; then
	yum install -y gmp-c++ gmp-devel clang-devel-19.1.7 llvm-devel-19.1.7
elif [ -e "$(which apk)" ]; then
	apk add gmp-dev clang17-dev llvm17-dev
fi

ROOT="$(git rev-parse --show-toplevel)"
THIRD_PARTY="$ROOT/third_party"
PREFIX="$THIRD_PARTY/opt"

cd "$THIRD_PARTY"
git clone git://repo.or.cz/pet.git

cd "$THIRD_PARTY/pet"
./get_submodules.sh
./autogen.sh
./configure --prefix="$PREFIX"
make -j install
