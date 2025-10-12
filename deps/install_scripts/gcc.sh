#!/usr/bin/bash

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"
BUILD_FILES="$(git rev-parse --show-toplevel)/deps/build_files"
mkdir -p "$BUILD_FILES"

pushd "$BUILD_FILES" || exit
wget -c https://ftp.tsukuba.wide.ad.jp/software/gcc/releases/gcc-14.2.0/gcc-14.2.0.tar.gz
tar xvf gcc-14.2.0.tar.gz
pushd gcc-14.2.0 || exit
./contrib/download_prerequisites
mkdir objdir
pushd objdir || exit
"$PWD"/../configure --disable-multilib  --enable-host-shared --prefix="$TADASHI_DEPS_PREFIX"
make
make install
popd || exit
popd || exit
rm -rf gcc-14.2.0
popd || exit
