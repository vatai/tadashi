#! /usr/bin/bash
set -x
set -e

ROOT=llvm-for-poly
BRANCH=llvmorg-10.0.0
PREFIX="$(pwd)/${ROOT}/opt"
cmake_args=(
    -G Ninja
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX="${PREFIX}"
    # -DLLVM_ENABLE_PROJECTS=';clang-tools-extra;compiler-rt;lld;polly;debuginfo-tests;libunwind;lldb'
    -DLLVM_ENABLE_PROJECTS='clang;libcxxabi;libcxx'
    # -DLLVM_BUILD_LLVM_DYLIB=ON
    # -DLLVM_LINK_LLVM_DYLIB=ON
    -DLLVM_BUILD_STATIC=ON
    -DLLVM_INSTALL_UTILS=ON
    -DLLVM_ENABLE_RTTI=ON
    -DLLVM_ENABLE_FFI=ON
    # -DLLVM_BUILD_TESTS=ON
    -DLLVM_PARALLEL_LINK_JOBS=1
    # -DCMAKE_CXX_FLAGS=-stdlib=libc++
    # -DLLVM_BINUTILS_INCDIR=/usr/include
)

CLANG_PREFIX="${HOME}/other-code/llvm-for-poly/opt/"

# rm -fr pluto
# git clone git@github.com:bondhugula/pluto.git

# rm -rf ${ROOT}
# git clone -b ${BRANCH} https://github.com/llvm/llvm-project.git ${ROOT}
wget https://raw.githubusercontent.com/archlinux/svntogit-packages/packages/llvm11/trunk/utils-benchmark-fix-missing-include.patch



pushd ${ROOT}

rm -rf build "${PREFIX}"

git checkout ${BRANCH} ############
git reset --hard
patch -Np1 -i ../utils-benchmark-fix-missing-include.patch

# CC=clang CXX=clang++
cmake -S llvm -B build "${cmake_args[@]}"
cmake --build build
ninja -C build install

popd
echo ">>> Finished building LLVM! <<<"


pushd pluto

git submodule init
git submodule update

./autogen.sh

configure_args=(
    --enable-debug
    --with-clang-prefix=${CLANG_PREFIX}
    )

./configure "${configure_args[@]}"
make -j
make -j test

popd
