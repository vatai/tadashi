from tadashi.pet cimport p_pet_scop
from libcpp.string cimport string

cdef extern from "scop.h":
    cdef cppclass Scop:
        Scop(p_pet_scop scop)
        string to_string()
