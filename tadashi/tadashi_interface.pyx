# distutils: language = c++

from libcpp.vector cimport vector

cdef extern from "../include/ctadashi.h":
    cdef vector[int] buz(int n)

def buz_wrap(n):
    v = buz(n)
    return list(v)
