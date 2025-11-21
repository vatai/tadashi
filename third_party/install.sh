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
curl https://repo.or.cz/isl.git/snapshot/15f1e39bed3997f773056d3fd127f38967adaa8a.tar.gz -o isl.tgz
curl https://repo.or.cz/pet.git/snapshot/b85d6e89cfd95c7228216307faa6e95caecbecf9.tar.gz -o pet.tgz
rm -fr isl pet
tar xzf isl.tgz && mv isl-* isl
tar xzf pet.tgz && mv pet-* pet

cd "$THIRD_PARTY/isl"
./autogen.sh
./configure --prefix="$PREFIX"
make -j install


cd "$THIRD_PARTY/pet"
./autogen.sh
./configure --prefix="$PREFIX" --with-clang-prefix="$CLANG_PREFIX" --with-isl-prefix="$PREFIX"
make -j install
