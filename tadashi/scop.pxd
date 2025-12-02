from tadashi cimport pet

cdef class Scop:
    cdef pet.scop _scop
    cdef Scop set_scop(self, pet.scop ptr)

