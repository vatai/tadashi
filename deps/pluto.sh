#! /usr/bin/bash
set -x
set -e

mkdir_ok_if_exists ()
{
    [ -e "$1" ] || mkdir -p "$1"
}

ROOT=$(pwd)
DOWNLOAD="${ROOT}/downloads"
OPT="${ROOT}/opt"
SRC="${ROOT}/src"
PATCH="${ROOT}/patches"
BUILD="${ROOT}/build"
mkdir_ok_if_exists "$DOWNLOAD"
mkdir_ok_if_exists "${OPT}"
mkdir_ok_if_exists "${SRC}"
mkdir_ok_if_exists "${PATCH}"
mkdir_ok_if_exists "${BUILD}"

LLVM_BRANCH="9.0.1"
LLVM_EXT="tar.xz"
LLVM_FILE="llvm-project-${LLVM_BRANCH}"
LLVM_URL_DIR="https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_BRANCH}"
LLVM_URL="${LLVM_URL_DIR}/${LLVM_FILE}.${LLVM_EXT}"
LLVM_PREFIX="${OPT}/${LLVM_FILE}"
LLVM_EXTRACTED="llvm-project-${LLVM_BRANCH}"

cmake_args=(
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
# patch -Np1 -i ../utils-benchmark-fix-missing-include.patch
# CC=clang CXX=clang++
cmake -S llvm -B build "${cmake_args[@]}"
cmake --build build
ninja -C build install

popd
popd

# rm -fr pluto
pushd ${BUILD}
git clone git@github.com:bondhugula/pluto.git
git submodule init --update

./autogen.sh

configure_args=(
    --prefix=${PLUTO_PREFIX}
    --enable-debug
    --with-clang-prefix=${LLVM_PREFIX}
    --with-pet=bundled
    --with-isl=bundled
    --enable-shared-barvinok
)

./configure "${configure_args[@]}"
make -j
make -j test
pushd pluto
popd
popd


