# -*- mode:cython -*-

from tadashi.ccscop cimport ccScop
from tadashi cimport isl

cdef class Scop:
  @staticmethod
  cdef Scop create(ccScop *ptr)
  cdef isl.isl_schedule_node *_cur(self)
  #
  cdef ccScop *ptr_ccscop
