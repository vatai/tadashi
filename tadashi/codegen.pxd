# -*- mode:cython -*-

from tadashi cimport isl, pet

cdef extern from "codegen.h":
    isl.printer codegen(isl.printer p, pet.scop scop, isl.schedule schedule);
