# distutils: language=c++
import os
from pathlib import Path

import cython
from cython.cimports.libc.stdio import FILE, fclose, fopen
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.ccscop import ccScop
from cython.cimports.tadashi.codegen import codegen
from cython.cimports.tadashi.scop import Scop

ABC_ERROR_MSG = "Translator is an abstract base class, use a derived class."
DOUBLE_SET_SOURCE = "Translator.set_source() should only be called once."


@cython.cclass
class Translator:
    """Translator base class."""

    ccscops = cython.declare(vector[ccScop])
    scops = cython.declare(list[Scop], visibility="public")
    ctx: isl.ctx
    source: str

    def __dealloc__(self):
        self.ccscops.clear()
        if self.ctx is not cython.NULL:
            isl.isl_ctx_free(self.ctx)

    @staticmethod
    def _check_missing_file(path: str | Path):
        path = Path(path)
        if not path.exists():
            raise ValueError(f"{path} does not exist!")

    @staticmethod
    def _get_flags(flag: str, flags: list[str]) -> list[str]:
        """Get values of the certain compiler flags from compiler options."""
        defines = []
        for i, opt in enumerate(flags):
            if not opt.startswith(f"-{flag}"):
                continue
            if opt == f"-{flag}":
                if i + 1 >= len(flags):
                    raise ValueError(f"Empty -{flag} comiler option")
                defines.append(flags[i + 1])
            else:
                defines.append(opt[2:])
        return defines

    def set_source(self, source: str | Path, options: list[str]) -> Translator:
        """Do the bookkeeping of the init.

        This method should be called from the derived class as
        super().set_source() after populatin the `ccScop`s.

        """
        self._check_missing_file(source)
        if self.ccscops.size():
            raise RuntimeError(DOUBLE_SET_SOURCE)
        self.source = str(source)
        self.scops = []
        self.ccscops.clear()
        self._populate_ccscops(str(source), options)
        for idx in range(self.ccscops.size()):
            ptr = cython.address(self.ccscops[idx])
            self.scops.append(Scop.create(ptr))
        return self

    def generate_code(self, input_path, output_path):
        raise NotImplementedError(ABC_ERROR_MSG)

    def set_include_paths(self, include_paths: list[str]):
        return self


@cython.cclass
class Pet(Translator):
    autodetect: bool

    def __init__(self, autodetect: bool = False):
        self.autodetect = autodetect

    def __copy__(self):
        cls = self.__class__
        return cls(self.autodetect)

    @cython.ccall
    def _populate_ccscops(self, source: str, options: list[str]):
        self.ctx = pet.isl_ctx_alloc_with_pet_options()
        if self.ctx is cython.NULL:
            raise MemoryError()
        # Set includes
        include_paths = self._get_flags("I", options)
        includes_str = ":".join([p for p in include_paths])
        prev_include_path = os.getenv("C_INCLUDE_PATH", "")
        os.environ["C_INCLUDE_PATH"] = includes_str
        if prev_include_path:
            os.environ["C_INCLUDE_PATH"] += f":{prev_include_path}"
        # Set defines
        for define in self._get_flags("D", options):
            pet.pet_options_append_defines(self.ctx, define.encode())
        # Set autodetect
        opt = 1 if self.autodetect else 0
        pet.pet_options_set_autodetect(self.ctx, opt)
        # Fill self.ccscops
        rv = pet.pet_transform_C_source(
            self.ctx,
            source.encode(),
            fopen("/dev/null".encode(), "w"),
            self._extract_scops_callback,
            cython.address(self.ccscops),
        )
        if -1 == rv:
            raise ValueError(
                f"Something went wrong while parsing the {source}. Is the file syntactically correct?"
            )

    @staticmethod
    @cython.cfunc
    @cython.exceptval(check=False)
    def _extract_scops_callback(
        p: isl.printer,
        scop: pet.scop,
        user: cython.p_void,
    ) -> isl.printer:
        vec = cython.cast(cython.pointer[vector[ccScop]], user)
        vec.emplace_back(scop)
        return p

    @cython.ccall
    def generate_code(self, input_path: str, output_path: str) -> int:
        r: int = 0
        scop_idx: int = 0
        output_file = cython.declare(cython.pointer[FILE])
        output_file = fopen(output_path.encode(), "w")
        scop_ptr = self.ccscops.data()
        r = pet.pet_transform_C_source(
            self.ctx,
            input_path.encode(),
            output_file,
            self._codegen_callback,
            cython.address(scop_ptr),
        )
        fclose(output_file)
        return r

    @staticmethod
    @cython.cfunc
    @cython.exceptval(check=False)
    def _codegen_callback(
        p: isl.printer,
        scop: pet.scop,
        user: cython.p_void,
    ) -> isl.printer:
        # `pptr` is a pointer to the "pointer in the outside function
        # pointing to the ccScop objects'
        pptr = cython.cast(cython.pointer[cython.pointer[ccScop]], user)
        ccscop = cython.operator.dereference(pptr)

        # todo: remove
        node = ccscop.current_node
        sn = isl.isl_schedule_node_to_str(node)
        # print(f"{sn=}")

        if not scop or not p:
            return isl.isl_printer_free(p)
        if not ccscop.modified:
            p = pet.pet_scop_print_original(scop, p)
        else:
            sched = isl.isl_schedule_node_get_schedule(ccscop.current_node)
            p = codegen(p, scop, sched)
        pet.pet_scop_free(scop)

        # increment the outer pointer.
        cython.operator.postincrement(cython.operator.dereference(pptr))
        return p
