#! /usr/bin/bash

source set_env.src
source llvm.src

set_env "${LLVM_PREFIX}"

PLUTO_EXT="tar.gz"
PLUTO_VERSION="0.11.4"
PLUTO_PREFIX="${OPT}/pluto-${PLUTO_VERSION}"

PLUTO_CONFIGURE_ARGS=(
    --prefix=${PLUTO_PREFIX}
    --with-clang-prefix=${LLVM_PREFIX}
)

pushd ${BUILD}
[ -e pluto ] || git clone --recurse-submodule git@github.com:bondhugula/pluto.git
pushd pluto

./autogen.sh
./configure "${PLUTO_CONFIGURE_ARGS[@]}"
make -j LDFLAGS="-lclangFrontend -lclangBasic -lclangLex -lclangDriver"
make -j test

rm -rf "${PLUTO_PREFIX}"
make install

popd
popd
