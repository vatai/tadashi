#!/usr/bin/bash

rm -rf "${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}"
rm -rf "${BUILD_FILES:-$(git rev-parse --show-toplevel)/deps/build_files}"
SCRIPTS_DIR=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/install_scripts}
"${SCRIPTS_DIR}/gmp.sh"
"${SCRIPTS_DIR}/llvm.sh"
"${SCRIPTS_DIR}/python.sh"
"${SCRIPTS_DIR}/swig.sh"
