#! /usr/bin/bash

source llvm.src

CONFIGURE_ARGS=(
    --with-clang=system
    --enable-shared-barvinok
)

pushd ${BUILD}

[ -e barvinok ] || git clone --recurse-submodules git://repo.or.cz/barvinok.git

pushd barvinok
./get_submodules.sh
./autogen.sh
./configure ${CONFIGURE_ARGS[@]}
bear -- make -j

popd
popd
