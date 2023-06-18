#! /usr/bin/bash

source llvm.src

CONFIGURE_ARGS=(
    --with-clang=system
    --with-pet=bundled
    --enable-shared-barvinok
)

pushd ${BUILD}

[ -e barvinok ] || git clone --recurse-submodules git://repo.or.cz/barvinok.git

pushd barvinok
./get_submodules.sh
autoupdate
./autogen.sh
./configure ${CONFIGURE_ARGS[@]}
# bear --
make -j
make isl.py

popd
popd
