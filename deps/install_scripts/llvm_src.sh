#!/usr/bin/bash

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"

pushd /tmp || exit
# git clone --depth 1 --branch llvmorg-19.1.7 https://github.com/llvm/llvm-project.git
wget -c https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.7/llvm-project-19.1.7.src.tar.xz
tar xvf llvm-project-19.1.7.src.tar.xz
pushd llvm-project-19.1.7.src || exit
cmake -S llvm -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="${TADASHI_DEPS_PREFIX}" -DLLVM_ENABLE_PROJECTS=clang
ninja -C build install
popd || exit
popd || exit

