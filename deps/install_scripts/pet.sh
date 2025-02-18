#!/usr/bin/bash

CONFIGURE_ARGS=(
  --enable-shared
  --prefix="$1"
  --with-isl="$2"
  --with-llvm="$3"
)

./get_submodules.sh
./autogen.sh
./configure "${CONFIGURE_ARGS[@]}"
make -j
make -j install

