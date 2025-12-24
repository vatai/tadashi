# -*- mode:cython -*-

from tadashi cimport isl, pet

cdef extern from "src/ccscop.h":
    cdef cppclass ccScop:
        # methods

        ccScop() except +
        ccScop(pet.scop *ps) except +

        void reset() except +
        void rollback() except +
        bint check_legality();
        # members
        isl.isl_schedule_node *current_node
        isl.isl_schedule_node *tmp_node
        bint current_legal
        bint tmp_legal
        int modified
