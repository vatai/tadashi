#!/usr/bin/bash
set -e

PREFIX=${PREFIX:-$(git rev-parse --show-toplevel)/opt/gnu-mpi}
mkdir -p "$PREFIX"

BUILD_FILES="/tmp/$(whoami)"
mkdir -p "$BUILD_FILES"
pushd "$BUILD_FILES" || exit
VERSION=5.0
EXT=.tar.bz2
FILE="openmpi-${VERSION}.10${EXT}"
wget -c "https://download.open-mpi.org/release/open-mpi/v${VERSION}/${FILE}"
tar xvf "$FILE"

pushd "${FILE%$EXT}" || exit
CC=gcc CXX=g++ FC=gfortran ./configure --prefix="$PREFIX"
make -j
make install
popd || exit
popd || exit

