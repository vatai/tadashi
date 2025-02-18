#!/usr/bin/bash

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"

module load system/genoa mpi/mpich-x86_64
set_env /home/users/emil.vatai/code/tadashi/deps/opt

pushd /tmp || exit
wget -c https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tar.xz
tar xvf  Python-3.12.0.tar.xz
pushd Python-3.12.0 || exit
./configure --enable-shared --prefix="${TADASHI_DEPS_PREFIX}"
make -j
make install
popd || exit
rm -rf Python-3.12.0
popd || exit
