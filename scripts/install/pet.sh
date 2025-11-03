#!/usr/bin/bash

# The args:
# $REPO/ctadashi
# $REPO/ctadashi/lib
# $REPO/deps/opt  # make sure you have llvm here first!

set -x
CONFIGURE_ARGS=(
  --enable-shared
  --prefix="$1" # ${CTADASHI_INSTALL_PREFIX}
  --libdir="$2" # ${CTADASHI_INSTALL_PREFIX}/${CMAKE_INSTALL_LIBDIR}
  --with-clang-prefix="$3" # ${CMAKE_SOURCE_DIR}/deps/opt
)
./get_submodules.sh
git -C ./isl checkout 15f1e39bed3997f773056d3fd127f38967adaa8a
./autogen.sh
./configure "${CONFIGURE_ARGS[@]}"
make -j
make -j install

