from tadashi.ccscop cimport ccScop

cdef class Scop:
  @staticmethod
  cdef Scop create(ccScop *ptr)
  cdef ccScop *ptr
