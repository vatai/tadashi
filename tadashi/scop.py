import cython
from cython.cimports.libc.stdlib import free  # todo: remove
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.tadashi_scop import TadashiScop
from cython.cimports.tadashi.transformations import *

PtrTScop = cython.typedef(cython.pointer(TadashiScop))


@cython.cclass
class Scop:
    ptr: PtrTScop

    def __dealloc__(self):
        if self.ptr != cython.NULL:
            free(self.ptr)

    @staticmethod
    @cython.cfunc
    def create(ptr: PtrTScop):
        scop = Scop()
        scop.ptr = ptr
        return scop

    @cython.cfunc
    def init(self, ptr: PtrTScop) -> Scop:
        self.ptr = ptr
        return self

    # def __repr__(self):
    #     sched = cython.declare(isl.schedule)
    #     sched = pet.pet_scop_get_schedule(self.ptr.scop)
    #     repr = isl.isl_schedule_to_str(sched)
    #     isl.isl_schedule_free(sched)
    #     return repr.decode()

    # def free_scop(self):
    #     if self.scop != cython.NULL:
    #         self.scop = pet.pet_scop_free(self.scop)

    # def foobar_transform(self, node_idx: int):
    #     sched = cython.declare(isl.schedule)
    #     sched = pet.pet_scop_get_schedule(self.ptr.scop)
    #     node = cython.declare(isl.schedule_node)
    #     node = isl.isl_schedule_get_root(sched)
    #     sched = isl.isl_schedule_free(sched)
    #     node = isl.isl_schedule_node_first_child(node)
    #     # print(isl.isl_schedule_node_to_str(node).decode())
    #     node = tadashi_interchange(node)
    #     result = isl.isl_schedule_node_to_str(node).decode()
    #     isl.isl_schedule_node_free(node)
    #     return result
