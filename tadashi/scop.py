import cython
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.ccscop import ccScop
from cython.cimports.tadashi.transformations import *


@cython.cclass
class Scop:
    ptr: cython.pointer(ccScop)

    @staticmethod
    @cython.cfunc
    def create(ptr: cython.pointer(ccScop)) -> Scop:
        scop = Scop()
        scop.ptr = ptr
        return scop

    def __repr__(self):
        node = self.ptr.current_node
        return isl.isl_schedule_node_to_str(node).decode()

    def foobar_transform(self, node_idx: int):  # TODO
        node = self.ptr.current_node
        node = isl.isl_schedule_node_first_child(node)
        node = tadashi_interchange(node)
        result = isl.isl_schedule_node_to_str(node).decode()
        self.ptr.current_node = node
        return result
