#! /usr/bin/bash

source ./llvm.src

LLVM_EXT="tar.xz"
LLVM_URL_DIR="https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_BRANCH}"
LLVM_URL="${LLVM_URL_DIR}/${LLVM_FILE}.${LLVM_EXT}"
LLVM_EXTRACTED="llvm-project-${LLVM_BRANCH}"
LLVM_CMAKE_ARGS=(
    -G Ninja
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX=${LLVM_PREFIX}
    -DLLVM_PARALLEL_COMPILE_JOBS=8
    -DLLVM_PARALLEL_LINK_JOBS=1
    -DLLVM_ENABLE_PROJECTS="clang"
)

wget -nc "${LLVM_URL}" -O "${DOWNLOAD}/${LLVM_FILE}.${LLVM_EXT}" || true

pushd "${BUILD}"
[ -e "${LLVM_EXTRACTED}" ] || tar xvf "${DOWNLOAD}/${LLVM_FILE}.${LLVM_EXT}"
pushd "${LLVM_EXTRACTED}"

mkdir -p build
sed -i.bak -e '/#include \"llvm\/Support\/Signals.h\"/i #include <stdint.h>' llvm/lib/Support/Signals.cpp
sed -i.bak -e "/#include <vector>/i #include <limits>" llvm/utils/benchmark/src/benchmark_register.h
cmake -S llvm -B build "${LLVM_CMAKE_ARGS[@]}"
cmake --build build

rm -rf "${LLVM_PREFIX}"
ninja -C build install

popd
popd
