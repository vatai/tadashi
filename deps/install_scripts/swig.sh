#!/urs/bin/bash

TADASHI_DEPS_PREFIX=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}
mkdir -p "$TADASHI_DEPS_PREFIX"

pushd /tmp || exit
wget http://prdownloads.sourceforge.net/swig/swig-4.3.0.tar.gz
tar xvf swig-4.3.0.tar.gz
pushd swig-4.3.0 || exit
./configure --prefix="$TADASHI_DEPS_PREFIX"
make -j
make install
popd || exit
rm -rf swig-4.3.0
popd || exit
