#! /usr/bin/bash

source ./llvm.src

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
