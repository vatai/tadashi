#!/bin/bash
#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N build_pluto
#PJM -L rscgrp=small
#PJM -L elapse=1:00:00
#PJM -L node=1
# #PJM --llio localtmp-size=40Gi
#PJM -j -S
set -e

function set_env ()
{
  export PATH="$1/bin${PATH:+:${PATH}}"
  export PATH="$1/bin64${PATH:+:${PATH}}"
  export LD_LIBRARY_PATH="$1/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  export LIBRARY_PATH="$1/lib${LIBRARY_PATH:+:${LIBRARY_PATH}}"
  export LD_LIBRARY_PATH="$1/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  export LIBRARY_PATH="$1/lib64${LIBRARY_PATH:+:${LIBRARY_PATH}}"
  export C_INCLUDE_PATH="$1/include${C_INCLUDE_PATH:+:${C_INCLUDE_PATH}}"
  export CPLUS_INCLUDE_PATH="$1/include${CPLUS_INCLUDE_PATH:+:${CPLUS_INCLUDE_PATH}}"
  export MAN_PATH="$1/man${MAN_PATH:+:${MAN_PATH}}"
  
}
source /home/apps/oss/llvm-v15.0.3/init.sh
export CC_FOR_BUILD="$CC"
export CXX_FOR_BUILD="$CXX"
export TMPDIR=/worktmp

set -x
ROOT="$(git rev-parse --show-toplevel)"
PREFIX="$ROOT/third_party/opt"
set_env "$PREFIX"
# mkdir -p "$TMPDIR/$(whoami)"
# BUILD_DIR="$(mktemp -d -p "$TMPDIR/$(whoami)")"
BUILD_DIR="$ROOT/third_party/build"
mkdir -p "$BUILD_DIR"
pushd "$BUILD_DIR" || exit

# build pluto
git clone https://github.com/bondhugula/pluto.git
pushd pluto || exit
git submodule update --init --recursive
# sed -i -e '/doc/d' cloog-isl/configure.ac
sed -i -e '/texinfo/Id' candl/configure.ac 
sed -i -e '/doc/d' candl/configure.ac 
sed -i -e 's/doc//' candl/Makefile.am
# cat cloog-isl/configure.ac
./autogen.sh
./configure --prefix="$PREFIX"
make -j$(nproc) install
popd || exit

popd || exit
