#!/bin/env python

import cython
from cython.cimports.tadashi import isl
from cython.cimports.tadashi.scop import Scop
from cython.cimports.tadashi.transformations import *

@cython.ccall
def tile_1d(scop: Scop, tile_size: int):
    scop.ptr_ccscop.current_node = tadashi_tile_1d(scop.ptr_ccscop.current_node, tile_size)

@cython.ccall
def tile_2d(scop: Scop, size1: int, size2: int):
    scop.ptr_ccscop.current_node = tadashi_tile_2d(scop.ptr_ccscop.current_node, size1, size2)

@cython.ccall
def tile_3d(scop: Scop, size1: int, size2: int, size3: int):
    scop.ptr_ccscop.current_node = tadashi_tile_3d(scop.ptr_ccscop.current_node, size1, size2, size3)

@cython.ccall
def interchange(scop: Scop):
    scop.ptr_ccscop.current_node = tadashi_interchange(scop.ptr_ccscop.current_node)

@cython.ccall
def full_fuse(scop: Scop):
    scop.ptr_ccscop.current_node = tadashi_full_fuse(scop.ptr_ccscop.current_node)

@cython.ccall
def fuse(scop: Scop, idx1: int, idx2: int):
    scop.ptr_ccscop.current_node = tadashi_fuse(scop.ptr_ccscop.current_node, idx1, idx2)

@cython.ccall
def full_split(scop: Scop):
    scop.ptr_ccscop.current_node = tadashi_full_split(scop.ptr_ccscop.current_node)

@cython.ccall
def split(scop: Scop, split_idx: int):
    scop.ptr_ccscop.current_node = tadashi_split(scop.ptr_ccscop.current_node, split_idx)

@cython.ccall
def scale(scop: Scop, scale: int):
    scop.ptr_ccscop.current_node = tadashi_scale(scop.ptr_ccscop.current_node, scale)

@cython.ccall
def full_shift_val(scop: Scop, val: int):
    scop.ptr_ccscop.current_node = tadashi_full_shift_val(scop.ptr_ccscop.current_node, val)

@cython.ccall
def partial_shift_val(scop: Scop, pa_idx: int, val: int):
    scop.ptr_ccscop.current_node = tadashi_partial_shift_val(scop.ptr_ccscop.current_node, pa_idx, val)

@cython.ccall
def full_shift_var(scop: Scop, var_idx: int, coeff: int):
    scop.ptr_ccscop.current_node = tadashi_full_shift_var(scop.ptr_ccscop.current_node, var_idx, coeff)

@cython.ccall
def partial_shift_var(scop: Scop, pa_idx: int, id_idx: int, coeff: int):
    scop.ptr_ccscop.current_node = tadashi_partial_shift_var(scop.ptr_ccscop.current_node, pa_idx, id_idx, coeff)

@cython.ccall
def full_shift_param(scop: Scop, param_idx: int, coeff: int):
    scop.ptr_ccscop.current_node = tadashi_full_shift_param(scop.ptr_ccscop.current_node, param_idx, coeff)

@cython.ccall
def partial_shift_param(scop: Scop, pa_idx: int, param_idx: int, coeff: int):
    scop.ptr_ccscop.current_node = tadashi_partial_shift_param(scop.ptr_ccscop.current_node, pa_idx, param_idx, coeff)

@cython.ccall
def set_parallel(scop: Scop, num_threads: int):
    scop.ptr_ccscop.current_node = tadashi_set_parallel(scop.ptr_ccscop.current_node, num_threads)

@cython.ccall
def set_loop_opt(scop: Scop, pos: int, opt: int):
    scop.ptr_ccscop.current_node = tadashi_set_loop_opt(scop.ptr_ccscop.current_node, pos, opt)

