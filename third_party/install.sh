#!/bin/sh
set -e
set -x

ROOT="$(git rev-parse --show-toplevel)"
THIRD_PARTY="$ROOT/third_party"
ISL_ORIGIN="$THIRD_PARTY/isl.bundle"
PREFIX="$THIRD_PARTY/opt"
CLANG_PREFIX="$(dirname "$(realpath "$(which llvm-config-19)")")"

if [ -e "$ROOT/third_party/isl.bundle" ]; then
	ISL_ORIGIN="$ROOT/third_party/isl.bundle"
	PET_ORIGIN="$ROOT/third_party/pet.bundle"
elif [ -e /project/third_party/isl.bundle ]; then
	ISL_ORIGIN=/project/third_party/isl.bundle
	PET_ORIGIN=/project/third_party/pet.bundle
else
	ISL_ORIGIN=https://repo.or.cz/isl.git
	PET_ORIGIN=https://repo.or.cz/pet.git
fi

if [ -e "$(which yum)" ]; then
	yum install -y gmp-c++ gmp-devel clang-devel-19.1.7 llvm-devel-19.1.7
fi
if [ -e "$(which apk)" ]; then
	apk add gmp-dev clang19-dev llvm19-dev
fi

cd /tmp
rm -fr isl
git init isl
cd isl
git remote add origin "$ISL_ORIGIN"
git fetch
git checkout master
./autogen.sh
./configure --prefix="$PREFIX"
make -j install


cd /tmp
rm -fr pet
git init pet
cd pet
git remote add origin "$PET_ORIGIN"
git fetch
git checkout master
./autogen.sh
./configure --prefix="$PREFIX" --with-clang-prefix="$CLANG_PREFIX" --with-isl-prefix="$PREFIX"
make -j install
