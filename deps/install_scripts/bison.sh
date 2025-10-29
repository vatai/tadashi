#!/usr/bin/bash
set -e

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"
BUILD_FILES="/tmp/$(whoami)"
mkdir -p "$BUILD_FILES"

pushd "$BUILD_FILES" || exit
wget -c https://mirrors.ustc.edu.cn/gnu/bison/bison-3.8.tar.xz
tar xvf bison-3.8.tar.xz
pushd bison-3.8 || exit
./configure --prefix="$TADASHI_DEPS_PREFIX"
make -j
make install
popd || exit
rm -rf bison-3.8
popd || exit
