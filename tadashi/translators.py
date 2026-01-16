# distutils: language=c++
import json
import os
import re
import subprocess
import tempfile
from importlib.resources import files
from pathlib import Path

import cython
from cython.cimports.libc.stdio import FILE, fclose, fopen
from cython.cimports.libcpp.string import string
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
        self.populate_ccscops(options)
        for idx in range(self.ccscops.size()):
            ptr = cython.address(self.ccscops[idx])
            self.scops.append(Scop.create(ptr))
        return self

    def generate_code(self, input_path, output_path):
        raise NotImplementedError(ABC_ERROR_MSG)


@cython.cclass
class Pet(Translator):
    autodetect: bool

    def __init__(self, autodetect: bool = False):
        self.autodetect = autodetect

    def __copy__(self):
        cls = self.__class__
        return cls(self.autodetect)

    def _set_includes(self, options: list[str]) -> str:
        """Temporarily extend `C_INCLUDE_PATH` environment variable.

        Args:

            options: compiler options.

        Returns:
            the original value of `C_INCLUDE_PATH`.

        Code enclosed with `_set_includes` and `_restore_includes`
        will have the extended `C_INCLUDE_PATH`.

        """
        llvm_include = str(files("tadashi") / "include")
        includes = self._get_flags("I", options)
        old_includes = os.getenv("C_INCLUDE_PATH", "")
        if old_includes:
            includes.append(old_includes)
        os.environ["C_INCLUDE_PATH"] = ":".join(includes + [llvm_include])
        return old_includes

    def _restore_includes(self, old_includes: str) -> None:
        """See _set_includes()."""
        os.environ["C_INCLUDE_PATH"] = old_includes

    @cython.ccall
    def populate_ccscops(self, options: list[str]):
        self.ctx = pet.isl_ctx_alloc_with_pet_options()
        if self.ctx is cython.NULL:
            raise MemoryError()
        # Set includes
        old_includes = self._set_includes(options)
        # Set defines
        for define in self._get_flags("D", options):
            pet.pet_options_append_defines(self.ctx, define.encode())
        # Set autodetect
        opt = 1 if self.autodetect else 0
        pet.pet_options_set_autodetect(self.ctx, opt)
        # Fill self.ccscops
        rv = pet.pet_transform_C_source(
            self.ctx,
            self.source.encode(),
            fopen("/dev/null".encode(), "w"),
            self._extract_scops_callback,
            cython.address(self.ccscops),
        )
        self._restore_includes(old_includes)
        if -1 == rv:
            raise ValueError(
                f"Something went wrong while parsing the {self.source}. Is the file syntactically correct?"
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
    def generate_code(
        self, input_path: str, output_path: str, options: list[str]
    ) -> int:
        r: int = 0
        scop_idx: int = 0
        output_file = cython.declare(cython.pointer[FILE])
        output_file = fopen(output_path.encode(), "w")
        scop_ptr = self.ccscops.data()
        old_includes = self._set_includes(options)
        r = pet.pet_transform_C_source(
            self.ctx,
            input_path.encode(),
            output_file,
            self._codegen_callback,
            cython.address(scop_ptr),
        )
        self._restore_includes(old_includes)
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


@cython.cclass
class Polly(Translator):
    compiler: str
    json_paths: list[bytes] = []
    cwd: str

    def __init__(self, compiler: str = "clang"):
        self.compiler = compiler

    def _run_compiler_and_opt(self, options: list[str]) -> str:
        self.ctx = pet.isl_ctx_alloc()
        if self.ctx is cython.NULL:
            raise MemoryError()
        self.cwd = tempfile.mkdtemp()
        compile_cmd = [
            str(self.compiler),
            "-S",
            "-emit-llvm",
            str(self.source),
            "-O1",
            "-o",
            "-",
        ]
        opt_cmd = [
            "opt",
            "-load",
            "LLVMPolly.so",
            "-disable-polly-legality",
            "-polly-canonicalize",
            "-polly-export-jscop",
            "-o",
            f"{self.source}.ll 2>&1",
        ]
        kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "cwd": self.cwd}
        compile_proc = subprocess.Popen(compile_cmd, **kwargs)
        opt_proc = subprocess.Popen(opt_cmd, stdin=compile_proc.stdout, **kwargs)
        compile_proc.wait()
        opt_proc.wait()
        stdout, stderr = opt_proc.communicate()
        compile_proc.stdout.close()
        compile_proc.stderr.close()
        opt_proc.stdout.close()
        opt_proc.stderr.close()
        if compile_proc.returncode:
            raise ValueError(
                f"Something went wrong while parsing the {self.source}. Is the file syntactically correct?"
            )
        return stderr.decode()

    @cython.ccall
    def _fill_json_paths(self, stderr: str):
        pat = re.compile(r".*to\s+'([^']*)'\.")
        for t in stderr.split("\n"):
            if not t:
                continue
            match = pat.search(t)
            if not match:
                raise ValueError(
                    "Something is wrong with `opt` output. Please raise an issue and mention this!"
                )
            file = match.group(1)
            self.json_paths.append(file)

    @cython.ccall
    def populate_ccscops(self, options: list[str]):
        stderr = self._run_compiler_and_opt(options)
        self._fill_json_paths(stderr)
        for file in self.json_paths:
            with open(file) as fp:
                jscop = json.load(fp)
            domain = isl.isl_union_set_empty_ctx(self.ctx)
            sched = isl.isl_union_map_empty_ctx(self.ctx)
            for stmt in jscop["statements"]:
                name = stmt["name"]
                tmp = stmt["domain"].encode()
                dmn = isl.isl_union_set_read_from_str(self.ctx, tmp)
                domain = isl.isl_union_set_union(domain, dmn)
                tmp = stmt["schedule"].encode()
                sch = isl.isl_union_map_read_from_str(self.ctx, tmp)
                sched = isl.isl_union_map_union(sched, sch)
            self.ccscops.emplace_back(domain, sched)
