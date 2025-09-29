#!/usr/bin/bash

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"

pushd /tmp || exit
wget -c http://prdownloads.sourceforge.net/swig/swig-4.3.0.tar.gz
tar xvf swig-4.3.0.tar.gz
pushd swig-4.3.0 || exit
cmake -S . -B build -G Ninja -DCMAKE_INSTALL_PREFIX="$TADASHI_DEPS_PREFIX"
ninja -C build install
popd || exit
popd || exit
