# distutils: language=c++

import cython
from cython.cimports.libc.stdio import fopen
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.scop import Scop

# ---------- Good stuffs starts here ----------


@cython.cclass
class Translator:
    _scops: list[Scop]  # C/C++ version (not visible to pyton)
    _ctx: isl.ctx = cython.declare(isl.ctx)
    source: str

    def __dealloc__(self):
        for s in self._scops:
            s.free_scop()
        if self._ctx is not cython.NULL:
            isl.isl_ctx_free(self._ctx)

    @property
    def scops(self):  # exposes self._scops to python
        return self._scops

    def set_source(self, source: str):
        self.source = source
        self._populate_scos(source)
        return self


@cython.cclass
class Pet(Translator):

    def _populate_scos(self, source: str):
        self._ctx = pet.isl_ctx_alloc_with_pet_options()
        if self._ctx is cython.NULL:
            raise MemoryError()
        vec = cython.declare(vector[pet.scop])
        pet.pet_transform_C_source(
            self._ctx,
            source.encode(),
            fopen("/dev/null".encode(), "w"),
            self._extract_scops,
            cython.address(vec),
        )
        self._scops = [Scop().init(ptr) for ptr in vec]

    @staticmethod
    @cython.cfunc
    @cython.exceptval(check=False)
    def _extract_scops(
        p: isl.printer,
        scop: pet.scop,
        user: cython.p_void,
    ) -> isl.printer:
        vec = cython.declare(cython.pointer[vector[pet.scop]])
        vec = cython.cast(cython.pointer[vector[pet.scop]], user)
        vec.emplace_back(scop)
        return p
