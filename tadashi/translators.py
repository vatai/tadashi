# distutils: language=c++
import datetime
import json
import os
import re
import shutil
import subprocess as subp
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
    source: Path

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
        self.source = Path(source).absolute()
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
            str(self.source).encode(),
            fopen("/dev/null".encode(), "w"),
            self._extract_scops_callback,
            cython.address(self.ccscops),
        )
        self._restore_includes(old_includes)
        if -1 == rv:
            raise ValueError(
                f"Something went wrong while parsing the {str(self.source)}. Is the file syntactically correct?"
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
    json_paths: list[Path] = []
    cwd: str

    def __init__(self, compiler: str = "clang"):
        self.compiler = compiler

    def _get_O1_bitcode(self) -> Path:
        output = Path(self.cwd) / self.source.with_suffix(".O1.bc").name
        if output.exists():
            return output
        cmd = [
            str(self.compiler),
            "-c",
            "-emit-llvm",
            str(self.source),
            "-O1",
            "-o",
            str(output),
        ]
        proc = subp.run(cmd, capture_output=True, cwd=self.cwd)
        if proc.returncode:
            msg = [
                f"{proc.stderr.decode()}",
                f"Something went wrong while parsing the {self.source}. ",
            ]
            raise ValueError(msg)
        return output

    @staticmethod
    def _polly():
        cmd = ["opt", "-load=LLVMPolly.so", "/dev/null", "-o=/dev/null"]
        ret = subp.run(cmd, stderr=subp.DEVNULL)
        final = ["opt"]
        if ret.returncode == 0:
            final.append("-load=LLVMPolly.so")
        final.append("-polly-canonicalize")
        return final

    def _export_jscops(self) -> str:
        cmd = self._polly()
        cmd.append(str(self._get_O1_bitcode()))
        cmd.append("-polly-export-jscop")
        cmd.append("-o=/dev/null")
        proc = subp.run(cmd, capture_output=True, cwd=self.cwd)
        return proc.stderr.decode()

    def _import_jscops(self) -> Path:
        output = Path(self.cwd) / self.source.with_suffix(".bc").name
        if output.exists():
            return output
        cmd = self._polly()
        cmd.append(str(self._get_O1_bitcode()))
        cmd.append("-polly-export-jscop")
        cmd.append(f"-o={output}")
        proc = subp.run(cmd, capture_output=True, cwd=self.cwd)
        return output

    def _generate_binary(self, output: str | Path, options: list[str]) -> int:
        cmd = ["clang"] + options
        input_path = str(self._import_jscops())
        cmd.append(input_path)
        cmd.append(f"-o{str(output)}")
        proc = subp.run(cmd)
        return proc.returncode

    @cython.ccall
    def _fill_json_paths(self, stderr: str):
        pat = re.compile(r".*to\s+'([^']*)'\.")
        for t in stderr.split("\n"):
            if not t:
                continue
            match = pat.search(t)
            if not match:
                raise ValueError(
                    f"Something is wrong with `opt` output. "
                    + "Please raise an issue and mention this!\n{stderr}"
                )
            file = match.group(1)
            self.json_paths.append(Path(file))

    def _proc_jscop(self, jscop):
        domain = isl.isl_union_set_empty_ctx(self.ctx)
        sched = isl.isl_union_map_empty_ctx(self.ctx)
        read = isl.isl_union_map_empty_ctx(self.ctx)
        write = isl.isl_union_map_empty_ctx(self.ctx)
        for stmt in jscop["statements"]:
            for acc in stmt["accesses"]:
                tmp = acc["relation"].encode()
                rel = isl.isl_union_map_read_from_str(self.ctx, tmp)
                if acc["kind"] == "read":
                    read = isl.isl_union_map_union(read, rel)
                elif acc["kind"] == "write":
                    write = isl.isl_union_map_union(write, rel)
                else:
                    raise SystemError(f"Error in JSCOP file ({acc["kind"]=})")
            dmn = isl.isl_union_set_read_from_str(self.ctx, stmt["domain"].encode())
            domain = isl.isl_union_set_union(domain, dmn)
            sch = isl.isl_union_map_read_from_str(self.ctx, stmt["schedule"].encode())
            sched = isl.isl_union_map_union(sched, sch)
        self.ccscops.emplace_back(domain, sched, read, write)

    @cython.ccall
    def populate_ccscops(self, options: list[str]):
        self.ctx = pet.isl_ctx_alloc()
        if self.ctx is cython.NULL:
            raise MemoryError()
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.cwd = tempfile.mkdtemp(prefix=f"tadashi-{timestamp}-")
        self._get_O1_bitcode()
        stderr = self._export_jscops()
        self._fill_json_paths(stderr)
        for file in self.json_paths:
            with open(self.cwd / file) as fp:
                jscop = json.load(fp)
            self._proc_jscop(jscop)

    @cython.ccall
    def generate_code(
        self, input_path: str, output_path: str, options: list[str]
    ) -> int:
        for scop_idx, jscop_path in enumerate(self.json_paths):
            jscop_path = self.cwd / jscop_path
            ccscop = self.ccscops[scop_idx]
            sched = isl.isl_schedule_node_get_schedule(ccscop.current_node)
            umap = isl.isl_schedule_get_map(sched)
            isl.isl_schedule_free(sched)
            sched_str = isl.isl_union_map_to_str(umap).decode()

            backup_path = jscop_path.with_suffix(jscop_path.suffix + ".bak")
            shutil.copy2(jscop_path, backup_path)

            with jscop_path.open("r", encoding="utf-8") as f:
                jscop = json.load(f)

            for stmt in jscop["statements"]:
                name = stmt["name"]
                uset = isl.isl_union_set_read_from_str(
                    self.ctx, stmt["domain"].encode()
                )
                stmt_map = isl.isl_union_map_intersect_domain_union_set(umap, uset)
                stmt["schedule"] = isl.isl_union_map_to_str(stmt_map).decode()
                isl.isl_union_map_free(stmt_map)

            with jscop_path.open("w", encoding="utf-8") as f:
                json.dump(jscop, f, indent=2)
        return self._generate_binary(output_path, options)
