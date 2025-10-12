#!/usr/bin/bash

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"
BUILD_FILES="$(git rev-parse --show-toplevel)/deps/build_files"
mkdir -p "$BUILD_FILES"

pushd "$BUILD_FILES" || exit
wget -c https://gmplib.org/download/gmp/gmp-6.3.0.tar.xz
tar xvf gmp-6.3.0.tar.xz
pushd gmp-6.3.0 || exit
./configure --prefix="$TADASHI_DEPS_PREFIX"
make -j
make install
popd || exit
rm -rf gmp-6.3.0
popd || exit
