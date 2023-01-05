#! /usr/bin/bash

source set_env.src
source llvm.src

set_env "${LLVM_PREFIX}"

PLUTO_EXT="tar.gz"
PLUTO_VERSION="0.11.4"
PLUTO_URL_DIR="https://github.com/bondhugula/pluto/archive/refs/tags"
PLUTO_URL_FILE="${PLUTO_VERSION}.${PLUTO_EXT}"
PLUTO_URL="${PLUTO_URL_DIR}/${PLUTO_URL_FILE}"
PLUTO_PREFIX="${OPT}/pluto-${PLUTO_VERSION}"

PLUTO_CONFIGURE_ARGS=(
    --prefix=${PLUTO_PREFIX}
    --with-clang-prefix=${LLVM_PREFIX}
    # --enable-debug
    # --with-pet=bundled
    # --with-isl=bundled
)

# wget -nc "${PLUTO_URL}" -O "${DOWNLOAD}/${PLUTO_FILE}.${PLUTO_EXT}"

pushd ${BUILD}
rm -fr pluto
[ -e pluto ] || git clone --recurse-submodule git@github.com:bondhugula/pluto.git

pushd pluto

echo ">>> autogen.sh <<<"
sh -x ./autogen.sh
echo "<<< autogen.sh >>>"

echo ">>> configure.sh <<<"
sh -x ./configure "${PLUTO_CONFIGURE_ARGS[@]}"
echo "<<< configure.sh >>>"

echo ">>> make <<<"
make -j V=1 SHELL="sh -x" LDFLAGS="-lclangFrontend -lclangBasic -lclangLex -lclangDriver"
echo "<<< make >>>"

make -j test

rm -rf "${PLUTO_PREFIX}"
make install

popd
popd
