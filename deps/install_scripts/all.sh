#!/usr/bin/bash

rm -rf "${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}"
rm -rf "${BUILD_FILES:-$(git rev-parse --show-toplevel)/deps/build_files}"
SCRIPTS_DIR=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/install_scripts}
"${SCRIPTS_DIR}/gmp.sh"
"${SCRIPTS_DIR}/llvm.sh"
"${SCRIPTS_DIR}/python.sh"
"${SCRIPTS_DIR}/swig.sh"

TADASHI_ROOT="$(git rev-parse --show-toplevel)"
CMAKE_ARGS=(
    -S "$TADASHI_ROOT"
    -B "$TADASHI_ROOT/build"
    -GNinja
    -DCMAKE_INSTALL_PREFIX="$TADASHI_ROOT"/ctadashi
    -DCALL_FROM_SETUP_PY=ON
)
cmake "${CMAKE_ARGS[@]}"
ninja -C "$TADASHI_ROOT/build" install
