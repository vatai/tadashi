#!/usr/bin/bash

cd pet
./get_submodules.sh
./autogen.sh
./configure
cd isl
./configure
make -j
cd ..
make -j
cd ..
