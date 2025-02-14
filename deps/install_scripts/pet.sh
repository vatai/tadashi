#!/usr/bin/bash

pet_BINARY_DIR=$1
PET_CONFIGURE_WITH_ISL=$2

./autogen.sh
./configure --prefix="${pet_BINARY_DIR}" --with-isl="${PET_CONFIGURE_WITH_ISL}"
make -j
make -j install

