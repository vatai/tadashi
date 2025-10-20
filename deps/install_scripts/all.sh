#!/usr/bin/bash
#SBATCH -p genoa
#SBATCH -N 1
#SBATCH -t 2:30:00
# #SBATCH -o %x-%j.txt
# #SBATCH -e %x-%j.txt
set -e

if [[ $HOSTNAME == login* ]]; then
    echo "DO NOT RUN THIS ON LOGIN NODE. Use `sbatch .../all.sh`"
    exit 1
fi

TADASHI_ROOT="$(git rev-parse --show-toplevel)"
rm -rf "${TADASHI_DEPS_PREFIX:-$TADASHI_ROOT/deps/opt}"
# rm -rf "${BUILD_FILES:-$TADASHI_ROOT/deps/build_files}"

source "$TADASHI_ROOT/scripts/genoa.source"

SCRIPTS_DIR=${TADASHI_DEPS_PREFIX:-$TADASHI_ROOT/deps/install_scripts}
"${SCRIPTS_DIR}/gmp.sh"
"${SCRIPTS_DIR}/llvm_src.sh"
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
