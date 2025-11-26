import cython
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.transformations import *


@cython.cclass
class Scop:
    def __init__(self):
        self._scop = cython.NULL

    def set_scop(self, ptr):
        self._scop = ptr

    def __repr__(self):
        sched = cython.declare(isl.schedule)
        sched = pet.pet_scop_get_schedule(self._scop)
        repr = isl.isl_schedule_to_str(sched)
        isl.isl_schedule_free(sched)
        return repr.decode()

    def free_scop(self):
        if self._scop != cython.NULL:
            self._scop = pet.pet_scop_free(self._scop)

    def transform(self, node_idx):
        sched = cython.declare(isl.schedule)
        sched = pet.pet_scop_get_schedule(self._scop)
        node = cython.declare(isl.schedule_node)
        node = isl.isl_schedule_get_root(sched)
        sched = isl.isl_schedule_free(sched)
        node = isl.isl_schedule_node_first_child(node)
        print(isl.isl_schedule_node_to_str(node).decode())
        node = tadashi_interchange(node)
        print(isl.isl_schedule_node_to_str(node).decode())
