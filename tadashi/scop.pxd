from tadashi cimport pet

cdef class Scop:
    cdef pet.scop pet_scop
    cdef void set_scop(self, pet.scop ptr)

