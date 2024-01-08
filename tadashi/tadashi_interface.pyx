cdef extern from "../src/ctadashi.cc":
    pass

# Declare the class with cdef
cdef extern from "../include/ctadashi.h"
    cdef cppclass Rectangle:
        Rectangle() except +
