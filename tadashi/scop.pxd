from tadashi cimport pet

cdef class Scop:
    cdef pet.scop _scop
    cdef void set_scop(self, pet.scop ptr)

