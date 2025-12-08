# -*- mode:cython -*-

from tadashi cimport isl, pet

cdef extern from "ccscop.h":
    cdef cppclass ccScop:
        # methods
        ccScop() except +
        ccScop(pet.scop ps) except +
        void dealloc() except +
        # members
        isl.isl_schedule_node *current_node
        bint modified
