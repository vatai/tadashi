# distutils: language=c++
import cython
from cython.cimports.libc.stdio import fopen
from cython.cimports.libcpp.string import string
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet

# from .scop import Scop

vec_p_pet_scop = cython.typedef(vector[pet.p_pet_scop])


@cython.cfunc
@cython.exceptval(check=False)
def _populate_scops(
    p: cython.pointer[isl.isl_printer],
    scop: pet.p_pet_scop,
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


@cython.cfunc
@cython.exceptval(check=False)
def pupulate_scops(
    infile: str, ctx: cython.pointer(isl.isl_ctx), scops: vec_p_pet_scop
) -> cython.void:
    pet.pet_transform_C_source(
        ctx,
        infile.encode(),
        fopen("/dev/null".encode(), "w"),
        _populate_scops,
        # cython.NULL,
        cython.address(scops),
    )


@cython.cclass
class App:
    _vec = cython.declare(vec_p_pet_scop)
    _ctx = cython.declare(cython.pointer[isl.isl_ctx])
    _scops = cython.declare(vec_p_pet_scop)

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

    # def append(self, x: int):
    #     self._vec.push_back(x)

    def foobar(self, infile: str, outfile: str):
        pet.pet_transform_C_source(
            self._ctx,
            infile.encode(),
            fopen(outfile.encode(), "w"),
            self.tr,
            # cython.NULL,
            cython.address(self._ctx),
        )
        return None


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
    source: str

    def __cinit__(self, source):
        self._ctx = pet.isl_ctx_alloc_with_pet_options()
        self.source = source
        # if self._ctx is cython.NULL:
        #     raise MemoryError()

        # print(f"{self._vec.size()=}")
        print(">>> created")

    def __dealloc__(self):
        print(self.source)
        if self._ctx is not cython.NULL:
            isl.isl_ctx_free(self._ctx)
            print("<<< destroyed")

    @property
    def scops(self):
        return [1, 2, 3]


# @cython.ccall
def mul(a, b):
    return a * b
