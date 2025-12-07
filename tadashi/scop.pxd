from tadashi.tadashi_scop cimport TadashiScop

cdef class Scop:
  @staticmethod
  cdef Scop create(TadashiScop *ptr)
  cdef TadashiScop *ptr
