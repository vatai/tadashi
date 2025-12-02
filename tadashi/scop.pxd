from tadashi cimport pet

cdef class Scop:
    cdef pet.scop _scop
    cdef Scop init(self, pet.scop ptr)

