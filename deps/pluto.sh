#! /usr/bin/bash

source set_env.src
set -x
set -e

ROOT=$(pwd)
DOWNLOAD="${ROOT}/downloads"
OPT="${ROOT}/pluto-opt"
BUILD="${ROOT}/build"
mkdir -p "$DOWNLOAD"
mkdir -p "$OPT"
mkdir -p "$BUILD"

LLVM_VERSION="15.0.0"
LLVM_URL="https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_VERSION}/llvm-project-${LLVM_VERSION}.src.tar.xz"
LLVM_CMAKE_ARGS=(
    -G Ninja
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX="$OPT"
    # -DLLVM_PARALLEL_COMPILE_JOBS=8
    -DLLVM_PARALLEL_LINK_JOBS=1
    -DLLVM_ENABLE_PROJECTS="clang;llvm;clang-tools-extra"
)

wget -nc "$LLVM_URL" -O "${DOWNLOAD}/$(basename $LLVM_URL)" || true

pushd "${BUILD}"
[ -e "llvm-project-${LLVM_VERSION}.src" ] || tar xvf "${DOWNLOAD}/$(basename $LLVM_URL)"
pushd "llvm-project-${LLVM_VERSION}.src"

mkdir -p build
# sed -i.bak -e '/#include \"llvm\/Support\/Signals.h\"/i #include <stdint.h>' llvm/lib/Support/Signals.cpp
# sed -i.bak -e "/#include <vector>/i #include <limits>" llvm/utils/benchmark/src/benchmark_register.h
cmake -S llvm -B build "${LLVM_CMAKE_ARGS[@]}"
cmake --build build

rm -rf "${LLVM_PREFIX}"
ninja -C build install

popd
popd

set_env "$OPT"

PLUTO_VERSION="0.13.0"
PLUTO_URL="https://github.com/bondhugula/pluto/releases/download/${PLUTO_VERSION}/pluto-${PLUTO_VERSION}.tgz"

PLUTO_CONFIGURE_ARGS=(
    --prefix=${OPT}
    --with-clang-prefix=${OPT}
    --enable-debug
)

wget -nc "$PLUTO_URL" -O "${DOWNLOAD}/$(basename $PLUTO_URL)" || true

pushd ${BUILD}
[ -e "pluto-$PLUTO_VERSION" ] || tar xvf "${DOWNLOAD}/$(basename $PLUTO_URL)"
pushd "pluto-$PLUTO_VERSION"

./autogen.sh
./configure "${PLUTO_CONFIGURE_ARGS[@]}"
make -j LDFLAGS="-lclangFrontend -lclangBasic -lclangLex -lclangDriver"
make -j test

rm -rf "${PLUTO_PREFIX}"
make install

popd
popd
