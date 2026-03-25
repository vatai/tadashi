# distutils: language=c++
import datetime
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from importlib.resources import files
from pathlib import Path

import cython
from cython.cimports.libc.stdio import FILE, fclose, fopen
from cython.cimports.libcpp.vector import vector
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.ccscop import ccScop
from cython.cimports.tadashi.codegen import codegen
from cython.cimports.tadashi.scop import Scop

from .passesparser import PassParser

# We can't use ABC because this is a @cython.cclass
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
        if not path.is_file():
            raise ValueError(f"{path} is not a file!")

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
        abs_path = Path(source).absolute()
        self._check_missing_file(abs_path)
        if self.ccscops.size():
            raise RuntimeError(DOUBLE_SET_SOURCE)
        self.source = abs_path
        self.scops = []
        self.ccscops.clear()
        self.populate_ccscops(options)
        for idx in range(self.ccscops.size()):
            ptr = cython.address(self.ccscops[idx])
            self.scops.append(Scop.create(ptr))
        return self

    def generate_code(
        self, input_path: str, output_path: Path, options: list[str]
    ) -> Path:
        raise NotImplementedError(ABC_ERROR_MSG)

    @cython.ccall
    def get_compiler(self) -> list[str]:
        raise NotImplementedError(ABC_ERROR_MSG)


@cython.cclass
class Pet(Translator):
    autodetect: bool

    def __init__(self, autodetect: bool = False):
        self.autodetect = autodetect

    def __copy__(self):
        cls = self.__class__
        return cls(self.autodetect)

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

    def legal(self):
        return all([bool(cc.current_legal) for cc in self.ccscops])

    @cython.ccall
    def generate_code(
        self, input_path: str, output_path: Path, options: list[str]
    ) -> Path:
        r: int = 0
        scop_idx: int = 0
        output_file = cython.declare(cython.pointer[FILE])
        output_file = fopen(str(output_path).encode(), "w")
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
        return output_path

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

    @cython.ccall
    def get_compiler(self) -> list[str]:
        return [os.getenv("CC", "gcc")]


@cython.cclass
class Polly(Translator):
    compiler: str
    json_paths: list[Path]
    tmpdir: Path
    before_polly_passes: str
    after_polly_passes: str
    logger: logging.Logger

    def __init__(self, compiler: str = "clang"):
        self.compiler = str(compiler)
        pp = PassParser()
        locs = pp.find("loop-rotate")
        before, after = pp.split(locs[1])
        self.before_polly_passes = pp.reassemble(before)
        self.after_polly_passes = pp.reassemble(after)
        self.logger = logging.getLogger(__name__)

    def _run(self, cmd: list[str], description: str):
        """cmd is command list, description is verb-ing"""
        self.logger.debug(f"Running: {' '.join(cmd)}")
        proc = subprocess.run(cmd, capture_output=True)
        self.logger.debug(f"stdout: {proc.stdout.decode()}")
        self.logger.debug(f"stderr: {proc.stderr.decode()}")
        if proc.returncode != 0:
            msg = [
                f"Something went wrong while [{description}]",
                "cmd: " + " ".join(cmd),
                f"returncode: {proc.returncode}",
                "stdout:",
                f"{proc.stdout.decode()}",
                "stderr",
                f"{proc.stderr.decode()}",
            ]
            raise ValueError("\n".join(msg))
        return proc

    @staticmethod
    def _sanitize(options: list[str]) -> list[str]:
        return options

    def _get_pre_polly_bc(self, options: list[str]) -> Path:
        compile_O0_bc = self.tmpdir / self.source.with_suffix(".O3.bc").name
        pre_polly_bc = self.tmpdir / self.source.with_suffix(".pre_polly.bc").name
        if pre_polly_bc.exists():
            return pre_polly_bc
        compiler_opts = self._compiler_options()
        sanitized = self._sanitize(options)
        compile_cmd = [self.compiler, *compiler_opts, *sanitized, "-c", "-emit-llvm"]
        compile_cmd += [str(self.source), "-o", str(compile_O0_bc)]
        self._run(compile_cmd, "compiling with O0")
        opt_cmd = ["opt", f"-passes={self.before_polly_passes}"]
        opt_cmd += [str(compile_O0_bc), f"-o={str(pre_polly_bc)}"]
        self._run(opt_cmd, "running pre polly opt passes")
        return pre_polly_bc

    def _export_jscops(self, options: list[str]) -> str:
        cmd = self._polly() + [
            str(self._get_pre_polly_bc(options)),
            "-polly-export-jscop",
            "-o=/dev/null",
        ]
        proc = self._run(cmd, "exporting jscops")
        return proc.stderr.decode()

    @cython.ccall
    def _fill_json_paths(self, stderr: str) -> list[Path]:
        json_paths = []
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
            json_paths.append(Path(file))
        return json_paths

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
        self.logger.debug("Start populating scops")
        self.ctx = pet.isl_ctx_alloc()
        if self.ctx is cython.NULL:
            raise MemoryError()
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.tmpdir = Path(tempfile.mkdtemp(prefix=f"tadashi-{timestamp}-"))
        self._get_pre_polly_bc(options)
        stderr = self._export_jscops(options)
        self.json_paths = self._fill_json_paths(stderr)
        for file in self.json_paths:
            self.logger.debug(f"Start processing jscop [{file.name}]")
            with open(self.tmpdir / file) as fp:
                jscop = json.load(fp)
            self._proc_jscop(jscop)
            self.logger.debug(f"Finish processing jscop [{file.name}]")
        self.logger.debug("Finish populating scops")

    def _compiler_options(self):
        for flang in ["mpifort", "mpif90", "mpif77", "flang", "flang-new"]:
            if flang in self.compiler:
                return ["-O0"]
        for clang in ["mpic++", "mpicc", "mpiCC", "mpicxx", "clang", "clang++", "acpp"]:
            if clang in self.compiler:
                return ["-O0", "-Xclang", "-disable-O0-optnone"]
        raise ValueError(f"Unsupported compiler: {self.compiler}")

    def _polly(self):
        opt_cmd = ["opt"]
        flags = ["-load=LLVMPolly.so", "/dev/null", "-o=/dev/null"]
        proc = subprocess.run(opt_cmd + flags, stderr=subprocess.DEVNULL)
        opt_cmd += ["-load=LLVMPolly.so"] if proc.returncode == 0 else []
        opt_cmd += [
            "-polly-canonicalize",
            f"-polly-import-jscop-dir={self.tmpdir}",
        ]
        return opt_cmd

    def legal(self) -> bool:
        input_path = str(self._get_pre_polly_bc([]))
        cmd = self._polly() + [
            input_path,
            "-polly-import-jscop",
            "-o=/dev/null",
        ]
        try:
            self._run(cmd, "checking legality")
        except ValueError as e:
            return False
        return True

    def _import_jscops(self, options: list[str]) -> Path:
        input_path = str(self._get_pre_polly_bc(options))
        post_polly_bc = self.tmpdir / self.source.with_suffix(".post_opt.bc").name

        polly_cmd = self._polly() + [
            input_path,
            "-polly-import-jscop",
            "-disable-polly-legality",
            "-polly-parallel-force",
            "-polly-codegen",
            f"-o={str(post_polly_bc)}",
        ]
        self._run(polly_cmd, "importing jscops")

        output = self.tmpdir / self.source.with_suffix(".bc").name

        opt_cmd = ["opt", f"-passes={self.after_polly_passes}"]
        opt_cmd += [str(post_polly_bc), f"-o={str(output)}"]
        opt_proc = self._run(opt_cmd, "running opt after jscops import")
        return output

    @cython.ccall
    def generate_code(
        self, input_path: str, output_path: Path, options: list[str]
    ) -> Path:
        for scop_idx, jscop_path in enumerate(self.json_paths):
            jscop_path = self.tmpdir / jscop_path
            backup_path = jscop_path.with_suffix(jscop_path.suffix + ".bak")
            shutil.copy2(jscop_path, backup_path)
            self._update_jscop(jscop_path, scop_idx)
        return self._compile_to_obj(output_path, options)

    @cython.cfunc
    def _update_jscop(self, jscop_path: Path, scop_idx: int):
        ccscop = self.ccscops[scop_idx]
        sched = isl.isl_schedule_node_get_schedule(ccscop.current_node)
        isl.isl_schedule_free(sched)
        umap = isl.isl_schedule_get_map(sched)
        with jscop_path.open("r", encoding="utf-8") as f:
            jscop = json.load(f)
        for stmt in jscop["statements"]:
            uset = isl.isl_union_set_read_from_str(self.ctx, stmt["domain"].encode())
            tmp = isl.isl_union_map_copy(umap)
            stmt_map = isl.isl_union_map_intersect_domain_union_set(tmp, uset)
            stmt["schedule"] = isl.isl_union_map_to_str(stmt_map).decode()
            isl.isl_union_map_free(stmt_map)
        with jscop_path.open("w", encoding="utf-8") as f:
            json.dump(jscop, f, indent=2)
        isl.isl_union_map_free(umap)

    def _compile_to_obj(self, output: Path, options: list[str]):
        output_path = Path(output).with_suffix(".o")
        input_path = str(self._import_jscops(options))
        cmd = ["llc", "-relocation-model=pic", "--filetype=obj"]
        cmd += [input_path, f"-o={str(output_path)}"]
        self._run(cmd, "generating assembly")
        return output_path

    @cython.ccall
    def get_compiler(self) -> list[str]:
        return [self.compiler, "-O3"]
