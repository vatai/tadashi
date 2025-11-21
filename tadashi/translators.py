# distutils: language=c++
import cython
from cython.cimports import isl, pet
from cython.cimports.libc.stdio import fopen
from cython.cimports.libcpp.vector import vector

_vec_t = cython.typedef(vector[cython.int])
pet_scop_p_vec = cython.typedef(vector[pet.pet_scop_p])


@cython.cclass
class App:
    _ctx = cython.declare(cython.pointer[isl.isl_ctx])
    _vec = cython.declare(_vec_t)
    _scops = cython.declare(pet_scop_p_vec)

    def __cinit__(self):
        self._ctx = pet.isl_ctx_alloc_with_pet_options()
        if self._ctx is cython.NULL:
            raise MemoryError()

        print(f"{self._vec.size()=}")
        print(">>> created")

    def __dealloc__(self):
        if self._ctx is not cython.NULL:
            isl.isl_ctx_free(self._ctx)
            print("<<< destroyed")


@cython.cclass
class PETApp(App):
    @staticmethod
    @cython.cfunc
    @cython.exceptval(check=False)
    def tr(
        p: cython.pointer[isl.isl_printer],
        scop: cython.pointer[pet.pet_scop],
        user: cython.p_void,
    ) -> cython.pointer[isl.isl_printer]:
        tmp = cython.declare(cython.pointer[vector[cython.int]])
        tmp = cython.cast(cython.pointer[vector[cython.int]], user)
        print(f"{tmp[0].size()=}")
        sched = pet.pet_scop_get_schedule(scop)
        s = isl.isl_schedule_to_str(sched)
        isl.isl_schedule_free(sched)
        print(s)
        pet.pet_scop_free(scop)
        return p

    def size(self):
        print(f"{self._vec.size()=}")

    def append(self, x: int):
        self._vec.push_back(x)

    def foobar(self, infile: str, outfile: str):
        pet.pet_transform_C_source(
            self._ctx,
            infile.encode(),
            fopen(outfile.encode(), "w"),
            self.tr,
            # cython.NULL,
            cython.address(self._vec),
        )


@cython.cclass
class LLVMApp(App):
    pass


@cython.cclass
class Translator:
    """`Translator`s extract `Scop`s from source files, and generate
    code from `Scop`s."""

    def get_scops(source: str):
        print("Tranlator.get_scops")


@cython.cclass
class Pet(Translator):
    """The `Pet` `Translator` is the PET backend of Tadashi."""

    _ctx = cython.declare(cython.pointer[isl.isl_ctx])

    def get_scops(source: str):
        print("Pet.get_scops")

    def __cinit__(self):
        self._ctx = pet.isl_ctx_alloc_with_pet_options()
        if self._ctx is cython.NULL:
            raise MemoryError()

        print(f"{self._vec.size()=}")
        print(">>> created")

    def __dealloc__(self):
        if self._ctx is not cython.NULL:
            isl.isl_ctx_free(self._ctx)
            print("<<< destroyed")
