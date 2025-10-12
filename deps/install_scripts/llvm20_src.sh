#!/usr/bin/bash
set -e

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt2}
mkdir -p "$TADASHI_DEPS_PREFIX"
BUILD_FILES="/tmp/$(whoami)"
mkdir -p "$BUILD_FILES"

pushd "$BUILD_FILES" || exit
version=20.1.0
# git clone --depth 1 --branch llvmorg-19.1.7 https://github.com/llvm/llvm-project.git
wget -c https://github.com/llvm/llvm-project/releases/download/llvmorg-$version/llvm-project-$version.src.tar.xz
tar xvf llvm-project-$version.src.tar.xz
pushd llvm-project-$version.src || exit
cmake -S llvm -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="${TADASHI_DEPS_PREFIX}" -DLLVM_ENABLE_PROJECTS="clang;flang;polly;mlir"
ninja -C build install
popd || exit
popd || exit

