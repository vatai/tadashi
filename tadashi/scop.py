import cython
from cython.cimports.tadashi import isl, pet


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
