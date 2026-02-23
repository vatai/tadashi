#!/bin/sh
set -e
set -x

if [ -e "$(which yum)" ]; then
    yum install -y gmp-c++ gmp-devel clang-devel-17.0.6 llvm-devel-17.0.6
    LICENSE_FILE=/usr/include/llvm/Support/LICENSE.TXT
elif [ -e "$(which apk)" ]; then
    apk add gmp-dev clang17-dev llvm17-dev
    LICENSE_FILE=/usr/lib/llvm17/include/llvm/Support/LICENSE.TXT
elif [ -e "$(which apt-get)" ]; then
    DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y git build-essential autoconf pkg-config libtool llvm-17-dev clang-17 libclang-17-dev libgmp-dev
    LICENSE_FILE=/usr/lib/llvm-17/build/utils/lit/LICENSE.TXT
fi

ROOT="$(git rev-parse --show-toplevel)"
THIRD_PARTY="$ROOT/third_party"
PREFIX="$THIRD_PARTY/opt"

cp -r "$(clang-17 -print-resource-dir)/include" "$ROOT/tadashi"
cp "$LICENSE_FILE" "$ROOT/tadashi/include"
CLANG_PREFIX="$(dirname "$(dirname "$(realpath "$(which llvm-config-17)")")")"
CLANG_OPTION=${CLANG_PREFIX:+--with-clang-prefix=$CLANG_PREFIX}

cd "$THIRD_PARTY"
git clone git://repo.or.cz/pet.git

cd "$THIRD_PARTY/pet"
./get_submodules.sh
./autogen.sh
./configure --prefix="$PREFIX" "$CLANG_OPTION"
make -j install
