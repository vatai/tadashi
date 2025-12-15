#!/bin/env python

import cython
from cython.cimports.tadashi import isl
from cython.cimports.tadashi.scop import Scop
from cython.cimports.tadashi.transformations import *


@cython.ccall
def interchange(scop: Scop):
    scop.scop.current_node = tadashi_interchange(scop.scop.current_node)
