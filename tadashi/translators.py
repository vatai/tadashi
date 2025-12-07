# distutils: language=c++

from pathlib import Path

import cython
from cython.cimports.libc.stdio import FILE, fclose, fopen
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.scop import Scop
from cython.cimports.tadashi.tadashi_scop import TadashiScop


@cython.cclass
class Translator:
    """Translator base class."""

    tadashi_scops: vector[TadashiScop]
    ctx: isl.ctx
    source: str

    def __dealloc__(self):
        # todo: return these two lines
        # for ts in self.tadashi_scops:
        #     pet.pet_scop_free(ts.scop)
        if self.ctx is not cython.NULL:
            isl.isl_ctx_free(self.ctx)

    @property
    @cython.ccall
    def scops(self) -> list[Scop]:
        """Exposes `Translator.scops` (which is a C++ object) to
        Python."""
        return [Scop.create(cython.address(ts)) for ts in self.tadashi_scops]

    def set_source(self, source: str | Path) -> Translator:
        self.source = str(source)
        self._populate_scops(str(source))
        return self

    def generate_code(self, input_path, output_path):
        pass


@cython.cclass
class Pet(Translator):

    @cython.ccall
    def _populate_scops(self, source: str):
        self.ctx = pet.isl_ctx_alloc_with_pet_options()
        if self.ctx is cython.NULL:
            raise MemoryError()
        pet.pet_transform_C_source(
            self.ctx,
            source.encode(),
            fopen("/dev/null".encode(), "w"),
            self._extract_scops_callback,
            cython.address(self.tadashi_scops),
        )

    @staticmethod
    @cython.cfunc
    @cython.exceptval(check=False)
    def _extract_scops_callback(
        p: isl.printer,
        scop: pet.scop,
        user: cython.p_void,
    ) -> isl.printer:
        vec = cython.declare(cython.pointer[vector[TadashiScop]])
        vec = cython.cast(cython.pointer[vector[TadashiScop]], user)
        vec.emplace_back(scop)
        return p

    @cython.ccall
    def generate_code(self, input_path: str, output_path: str) -> int:
        r: int = 0
        scop_idx: int = 0
        output_file = cython.declare(cython.pointer[FILE])
        output_file = fopen(output_path.encode(), "w")
        r = pet.pet_transform_C_source(
            self.ctx,
            input_path.encode(),
            output_file,
            self._codegen_callback,
            self.tadashi_scops.data(),
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
        # isl_ctx *ctx;
        # isl_schedule *sched;
        # Scop **si_ptr = (Scop **)user;
        # Scop *si = *si_ptr;
        # if (!scop || !p)
        #     return isl_printer_free(p);
        # if (!si->modified) {
        #     p = pet_scop_print_original(scop, p);
        # } else {
        #     sched = isl_schedule_node_get_schedule(si->current_node);
        #     p = codegen(p, si->scop->pet_scop, sched);
        # }
        # pet_scop_free(scop);
        # si_ptr++;
        return p
