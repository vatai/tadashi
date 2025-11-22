# distutils: language=c++
import cython
from cython.cimports.libc.stdio import fopen
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.scop import Scop

# ---------- Good stuffs starts here ----------


@cython.cclass
class Translator:
    """`Translator`s extract `Scop`s from source files, and generate
    code from `Scop`s."""

    source: str


@cython.cclass
class Pet(Translator):
    """The `Pet` `Translator` is the PET backend of Tadashi."""

    _ctx = cython.declare(cython.pointer[isl.isl_ctx])
    _scops = cython.declare(vector[Scop])

    def __cinit__(self, source):
        self._ctx = pet.isl_ctx_alloc_with_pet_options()
        if self._ctx is cython.NULL:
            raise MemoryError()
        self._scops.reserve(42)
        self.source = source
        pet.pet_transform_C_source(
            self._ctx,
            source.encode(),
            fopen("/dev/null".encode(), "w"),
            self._populate_scops,
            cython.address(self._scops),
        )
        print(">>> created TODO")

    @property
    def scops(self):
        rv = []
        # for i in range(self._scops.size()):
        #     rv.append(self._scops[i].to_string())
        return rv

    @staticmethod
    @cython.cfunc
    @cython.exceptval(check=False)
    def _populate_scops(
        p: isl.p_isl_printer,
        scop: pet.p_pet_scop,
        user: cython.p_void,
    ) -> isl.p_isl_printer:
        print("BBBBBOOO")
        vec = cython.declare(cython.pointer[vector[Scop]])
        vec = cython.cast(cython.pointer[vector[Scop]], user)
        vec.emplace_back(scop)
        return p

    def __dealloc__(self):
        print(self.source)
        del self._scops
        if self._ctx is not cython.NULL:
            isl.isl_ctx_free(self._ctx)
            print("<<< destroyed TODO")
