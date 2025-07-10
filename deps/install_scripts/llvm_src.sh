#!/usr/bin/bash

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"

version=20.1.8

pushd /tmp || exit
# git clone --depth 1 --branch llvmorg-${version} https://github.com/llvm/llvm-project.git
wget -c https://github.com/llvm/llvm-project/releases/download/llvmorg-${version}/llvm-project-${version}.src.tar.xz
tar xvf llvm-project-${version}.src.tar.xz
pushd llvm-project-${version}.src || exit
cmake -S llvm -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="${TADASHI_DEPS_PREFIX}" -DLLVM_ENABLE_PROJECTS="clang;flang;polly;mlir"
ninja -C build install
popd || exit
popd || exit

