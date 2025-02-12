#!/usr/bin/bash

rm -rf "${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/opt}"
SCRIPTS_DIR=${TADASHI_DEPS_PREFIX:-$(git rev-parse --show-toplevel)/deps/install_scripts}
"${SCRIPTS_DIR}/gmp.sh"
"${SCRIPTS_DIR}/llvm_src.sh"
"${SCRIPTS_DIR}/python.sh"
"${SCRIPTS_DIR}/swig.sh"

