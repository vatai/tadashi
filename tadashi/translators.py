# distutils: language=c++

import cython
from cython.cimports.libc.stdio import fopen
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.scop import Scop

# ---------- Good stuffs starts here ----------


@cython.cclass
class Pet:

    _scops: list[Scop]
    _ctx = cython.declare(cython.pointer[isl.isl_ctx])
    source: str

    def __cinit__(self, source):
        self._ctx = pet.isl_ctx_alloc_with_pet_options()
        self.source = source
        if self._ctx is cython.NULL:
            raise MemoryError()
        vec = cython.declare(vector[pet.scop])
        pet.pet_transform_C_source(
            self._ctx,
            source.encode(),
            fopen("/dev/null".encode(), "w"),
            self._populate_scops,
            cython.address(vec),
        )
        self._scops = []
        for ptr in vec:
            obj = Scop()
            obj.set_scop(ptr)
            self._scops.append(obj)

    def __dealloc__(self):
        self._scops.clear()
        if self._ctx is not cython.NULL:
            isl.isl_ctx_free(self._ctx)

    @property
    def scops(self):
        return self._scops

    @staticmethod
    @cython.cfunc
    @cython.exceptval(check=False)
    def _populate_scops(
        p: isl.p_isl_printer, scop: pet.scop, user: cython.p_void
    ) -> isl.p_isl_printer:
        vec = cython.declare(cython.pointer[vector[pet.scop]])
        vec = cython.cast(cython.pointer[vector[pet.scop]], user)
        vec.emplace_back(scop)
        return p
