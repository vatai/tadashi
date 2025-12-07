# -*- mode:cython -*-

from tadashi cimport pet

cdef extern from "tadashi_scop.h":
    cdef cppclass TadashiScop:
        TadashiScop() except +
        TadashiScop(pet.scop ps) except +
        pet.scop scop
