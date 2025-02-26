#!/bin/bash
set -e
export PYTHONPATH=.
VALGRIND_ARGS=(
    --leak-check=full
    --show-leak-kinds=all
    --track-origins=yes
    # --verbose
    # --log-file=valgrind-out.txt
    --keep-debuginfo=yes
)
TESTS=(
    tests.py.test_ctadashi.TestCtadashi.test_full_fuse
    tests.py.test_ctadashi.TestCtadashi.test_full_shift_param
    tests.py.test_ctadashi.TestCtadashi.test_full_shift_val
    tests.py.test_ctadashi.TestCtadashi.test_full_shift_var
    tests.py.test_ctadashi.TestCtadashi.test_fuse
    tests.py.test_ctadashi.TestCtadashi.test_interchange_1
    tests.py.test_ctadashi.TestCtadashi.test_partial_fuse
    tests.py.test_ctadashi.TestCtadashi.test_partial_shift_param
    tests.py.test_ctadashi.TestCtadashi.test_partial_shift_val
    tests.py.test_ctadashi.TestCtadashi.test_partial_shift_var
    tests.py.test_ctadashi.TestCtadashi.test_pluto_fig4
    tests.py.test_ctadashi.TestCtadashi.test_tile_1
    tests.py.test_ctadashi.TestCtadashi.test_tile_2
)

# for i in $(seq 0 12); do
#     # python -m unittest -v "${TESTS[$i]}"
#     valgrind ${VALGRIND_ARGS[@]} python -m unittest "${TESTS[$i]}" 2>&1 | tail
#     echo test "${TESTS[$i]}"
# done

valgrind ${VALGRIND_ARGS[@]} python -m unittest 2>&1 | tail
# valgrind ${VALGRIND_ARGS[@]} python examples/inputs/end2edn.py
