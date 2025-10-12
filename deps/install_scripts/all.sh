#!/usr/bin/bash

TADASHI_ROOT="$(git rev-parse --show-toplevel)"
rm -rf "${TADASHI_DEPS_PREFIX:-$TADASHI_ROOT/deps/opt}"
rm -rf "${BUILD_FILES:-$TADASHI_ROOT/deps/build_files}"
SCRIPTS_DIR=${TADASHI_DEPS_PREFIX:-$TADASHI_ROOT/deps/install_scripts}
source "$TADASHI_ROOT/scripts/genoa.source"
"${SCRIPTS_DIR}/gmp.sh"
"${SCRIPTS_DIR}/llvm.sh"
"${SCRIPTS_DIR}/python.sh"
"${SCRIPTS_DIR}/swig.sh"

CMAKE_ARGS=(
    -S "$TADASHI_ROOT"
    -B "$TADASHI_ROOT/build"
    -GNinja
    -DCMAKE_INSTALL_PREFIX="$TADASHI_ROOT"/ctadashi
    -DCALL_FROM_SETUP_PY=ON
)
cmake "${CMAKE_ARGS[@]}"
ninja -C "$TADASHI_ROOT/build" install
