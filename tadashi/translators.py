# distutils: language=c++

from pathlib import Path

import cython
from cython.cimports.libc.stdio import FILE, fclose, fopen
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.ccscop import ccScop
from cython.cimports.tadashi.scop import Scop


@cython.cclass
class Translator:
    """Translator base class."""

    ccscops: vector[ccScop]
    scops = cython.declare(list[Scop], visibility="public")
    ctx: isl.ctx
    source: str

    def __dealloc__(self):
        for idx in range(self.ccscops.size()):
            self.ccscops[idx].dealloc()
        if self.ctx is not cython.NULL:
            isl.isl_ctx_free(self.ctx)

    def set_source(self, source: str | Path) -> Translator:
        self.source = str(source)
        self._populate_ccscops(str(source))
        self.scops = []
        for idx in range(self.ccscops.size()):
            ptr = cython.address(self.ccscops[idx])
            self.scops.append(Scop.create(ptr))
        return self

    def generate_code(self, input_path, output_path):
        pass


@cython.cclass
class Pet(Translator):

    @cython.ccall
    def _populate_ccscops(self, source: str):
        self.ctx = pet.isl_ctx_alloc_with_pet_options()
        if self.ctx is cython.NULL:
            raise MemoryError()
        pet.pet_transform_C_source(
            self.ctx,
            source.encode(),
            fopen("/dev/null".encode(), "w"),
            self._extract_scops_callback,
            cython.address(self.ccscops),
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
        r = pet.pet_transform_C_source(
            self.ctx,
            input_path.encode(),
            output_file,
            self._codegen_callback,
            self.ccscops.data(),
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
        # isl_schedule *sched;
        # Scop **si_ptr = (Scop **)user;
        # Scop *si = *si_ptr;
        if not scop or not p:
            return isl.isl_printer_free(p)
        # if (!si->modified) {
        #     p = pet_scop_print_original(scop, p);
        # } else {
        #     sched = isl_schedule_node_get_schedule(si->current_node);
        #     p = codegen(p, si->scop->pet_scop, sched);
        # }
        # pet_scop_free(scop);
        # si_ptr++;
        return p
