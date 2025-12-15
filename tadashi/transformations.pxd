# -*- mode:cython -*-

from tadashi.isl cimport *

cdef extern from "transformations.h":
    cdef isl_schedule_node *tadashi_tile_1d(isl_schedule_node * node, int tile_size)
    cdef isl_schedule_node *tadashi_tile_2d(isl_schedule_node * node, int size1, int size2)
    cdef isl_schedule_node *tadashi_tile_3d(isl_schedule_node * node, int size1, int size2, int size3)
    cdef isl_schedule_node *tadashi_interchange(isl_schedule_node * node)
    cdef isl_schedule_node *tadashi_full_fuse(isl_schedule_node * node)
    cdef isl_schedule_node *tadashi_fuse(isl_schedule_node * node, int idx1, int idx2)
    cdef isl_schedule_node *tadashi_full_split(isl_schedule_node * node)
    cdef isl_schedule_node *tadashi_split(isl_schedule_node * node, int split)
    cdef isl_schedule_node *tadashi_scale(isl_schedule_node * node, long scale)
    cdef isl_schedule_node *tadashi_full_shift_val(isl_schedule_node * node, long val)
    cdef isl_schedule_node *tadashi_partial_shift_val(isl_schedule_node * node, int pa_idx, long val)
    cdef isl_schedule_node *tadashi_full_shift_var(isl_schedule_node * node, long var_idx, long coeff)
    cdef isl_schedule_node *tadashi_partial_shift_var(isl_schedule_node * node, int pa_idx, long id_idx, long coeff)
    cdef isl_schedule_node *tadashi_full_shift_param(isl_schedule_node * node, long param_idx, long coeff)
    cdef isl_schedule_node *tadashi_partial_shift_param(isl_schedule_node * node, int pa_idx, long param_idx, long coeff)
    cdef isl_schedule_node *tadashi_set_parallel(isl_schedule_node * node, int num_threads)
