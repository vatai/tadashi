#! /usr/bin/bash

source llvm.src

PLUTO_EXT="tar.gz"
PLUTO_VERSION="0.11.4"
PLUTO_URL_DIR="https://github.com/bondhugula/pluto/archive/refs/tags"
PLUTO_URL_FILE="${PLUTO_VERSION}.${PLUTO_EXT}"
PLUTO_URL="${PLUTO_URL_DIR}/${PLUTO_URL_FILE}"
PLUTO_PREFIX="${OPT}"

PLUTO_CONFIGURE_ARGS=(
    --prefix=${PLUTO_PREFIX}
    --enable-debug
    --with-clang-prefix=${LLVM_PREFIX}
    # --with-pet=bundled
    # --with-isl=bundled
)

# wget -nc "${PLUTO_URL}" -O "${DOWNLOAD}/${PLUTO_FILE}.${PLUTO_EXT}"

pushd ${BUILD}
rm -fr pluto
[ -e pluto ] || git clone --recurse-submodule git@github.com:bondhugula/pluto.git
pushd pluto

./autogen.sh
./configure "${PLUTO_CONFIGURE_ARGS[@]}"
make -j
make -j test
make install

popd
popd
