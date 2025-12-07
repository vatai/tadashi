# -*- mode:cython -*-

from tadashi cimport pet

cdef extern from "ccscop.h":
    cdef cppclass ccScop:
        ccScop() except +
        ccScop(pet.scop ps) except +
        pet.scop scop
        void dealloc() except +
