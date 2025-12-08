# -*- mode:cython -*-

from tadashi.isl cimport *

cdef extern from "transformations.h":
    cdef isl_schedule_node *tadashi_tile_2d(isl_schedule_node *node, int size1, int size2)
    cdef isl_schedule_node *tadashi_interchange(isl_schedule_node *node)
