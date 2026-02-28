#!/bin/bash
#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N tadashi_install
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
source /home/apps/oss/llvm-v19.1.4/init.sh
export CC_FOR_BUILD="$CC"
export CXX_FOR_BUILD="$CXX"

set -x
ROOT="$(git rev-parse --show-toplevel)"
set_env "$ROOT/deps/opt"
THIRD_PARTY="$ROOT/third_party"
PREFIX="$THIRD_PARTY/opt"

# cp -r "$(clang-19 -print-resource-dir)/include" "$ROOT/tadashi"
CLANG_PREFIX="$(dirname "$(dirname "$(realpath "$(which llvm-config)")")")"
CLANG_OPTION=${CLANG_PREFIX:+--with-clang-prefix=$CLANG_PREFIX}

cd "$THIRD_PARTY"
git clone git://repo.or.cz/pet.git

cd "$THIRD_PARTY/pet"
./get_submodules.sh
./autogen.sh
./configure --prefix="$PREFIX" "$CLANG_OPTION"
make -j install

