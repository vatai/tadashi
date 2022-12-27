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
    -DLLVM_PARALLEL_LINK_JOBS=1
    -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra;lld"
    -DLLVM_BUILD_LLVM_DYLIB=ON
)

pushd "${DOWNLOAD}"
wget -nc "${LLVM_URL}"
popd

pushd "${PATCH}"
wget -nc https://raw.githubusercontent.com/archlinux/svntogit-packages/packages/llvm11/trunk/utils-benchmark-fix-missing-include.patch
popd

pushd "${BUILD}"
[ -e "${LLVM_EXTRACTED}" ] || tar xvf "${DOWNLOAD}/${LLVM_FILE}.${LLVM_EXT}"
pushd "${LLVM_EXTRACTED}"

mkdir_ok_if_exists build
patch -Np1 -i "${PATCH}/utils-benchmark-fix-missing-include.patch" || true
# CC=clang CXX=clang++
cmake -S llvm -B build "${LLVM_CMAKE_ARGS[@]}"
cmake --build build
ninja -C build install

popd
popd
