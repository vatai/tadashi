#!/usr/bin/bash
set -e

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"
BUILD_FILES="/tmp/$(whoami)"
mkdir -p "$BUILD_FILES"

VERSION=19.1.1
CMAKE_ARGS=(
    -S llvm -B build -G Ninja
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX="${TADASHI_DEPS_PREFIX}"
    -DLLVM_ENABLE_PROJECTS="clang;flang;polly;mlir"
    # -DLLVM_PARALLEL_LINK_JOBS=2
)

pushd "$BUILD_FILES" || exit
# git clone --depth 1 --branch llvmorg-${VERSION} https://github.com/llvm/llvm-project.git
wget -c https://github.com/llvm/llvm-project/releases/download/llvmorg-${VERSION}/llvm-project-${VERSION}.src.tar.xz
tar xvf llvm-project-${VERSION}.src.tar.xz
pushd llvm-project-${VERSION}.src || exit
cmake "${CMAKE_ARGS[@]}"
ninja -C build install
popd || exit
popd || exit

