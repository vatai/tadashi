#!/usr/bin/bash
set -e

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"

BUILD_FILES="/tmp/$(whoami)"
mkdir -p "$BUILD_FILES"
pushd "$BUILD_FILES" || exit
wget -c https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.0/LLVM-19.1.0-Linux-X64.tar.xz
tar xvf LLVM-19.1.0-Linux-X64.tar.xz -C "$TADASHI_DEPS_PREFIX" --strip-components=1
popd || exit
