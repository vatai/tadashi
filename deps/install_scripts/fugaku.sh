#!/usr/bin/bash

#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N tadashi_install
#PJM -L rscgrp=small
#PJM -L elapse=1:00:00
#PJM -L node=1
# #PJM --llio localtmp-size=40Gi
#PJM -j -S
#PJM -m b,e --mail-list emil.vatai@gmail.com

set -e
set -x

if [[ $HOSTNAME == fn* ]]; then
    echo "DO NOT RUN THIS ON LOGIN NODE."
    exit 1
fi

export PATH=$HOME/bin.compute:$PATH

TADASHI_ROOT="$(git rev-parse --show-toplevel)"
# rm -rf "${TADASHI_DEPS_PREFIX:-$TADASHI_ROOT/deps/opt}"

source "$TADASHI_ROOT/scripts/fugaku.source"

# source /home/apps/oss/llvm-v19.1.4/init.sh
SCRIPTS_DIR=${TADASHI_DEPS_PREFIX:-$TADASHI_ROOT/deps/install_scripts}
"${SCRIPTS_DIR}/gmp.sh"
"${SCRIPTS_DIR}/python.sh"
"${SCRIPTS_DIR}/bison.sh"
"${SCRIPTS_DIR}/swig.sh"

rm -fr build ctadashi || true
CMAKE_ARGS=(
    -S "$TADASHI_ROOT"
    -B "$TADASHI_ROOT/build"
    -GNinja
    -DCMAKE_INSTALL_PREFIX="$TADASHI_ROOT"/ctadashi
    -DCALL_FROM_SETUP_PY=ON
)
cmake "${CMAKE_ARGS[@]}"
ninja -C "$TADASHI_ROOT/build" install
