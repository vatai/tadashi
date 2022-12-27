#! /usr/bin/bash

source llvm.src

PLUTO_PREFIX="${OPT}"

PLUTO_CONFIGURE_ARGS=(
    --prefix=${PLUTO_PREFIX}
    --enable-debug
    --with-clang-prefix=${LLVM_PREFIX}
    --with-pet=bundled
    --with-isl=bundled
    --enable-shared-barvinok
)

pushd "${DOWNLOAD}"
wget https://github.com/bondhugula/pluto/archive/refs/tags/0.11.4.tar.gz
popd

pushd ${BUILD}
rm -fr pluto
[ -e pluto ] || git clone --recurse-submodule git@github.com:bondhugula/pluto.git
pushd pluto

./autogen.sh
# ./configure "${PLUTO_CONFIGURE_ARGS[@]}"
# make -j
# make -j test

popd
popd
