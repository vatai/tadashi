#!/usr/bin/eval python
from pathlib import Path
from subprocess import PIPE, run

from tadashi.apps import App


class Snap(App):
    def __init__(self, source, target, compiler_options=[]):
        msg = "Target should be 1 or 3 based on which filme source points to (dim1_sweep.c or dim3_sweep.c)"
        assert target in [1, 3], msg
        self.target = target
        print(f"{include_path=}")
        include_path = self.mpi_include_paths()
        include_path += self.gcc_includes()
        self._finalize_object(
            source,
            include_paths=include_path,
            compiler_options=compiler_options,
        )

    def mpi_include_paths():
        result = run(["mpicc", "-compile_info"], stdout=PIPE)
        stdout = result.stdout.decode()
        opts = stdout.split()
        return [inc[2:] for inc in opts if inc.startswith("-I")]

    def gcc_includes():
        cmd = ["gcc", "-xc", "-E", "-v", "/dev/null"]
        result = run(["mpicc", "-compile_info"], stdout=PIPE)
        stdout = result.stdout.decode()
        include_paths = []
        collect = False
        for line in stdout.split("\n"):
            if collect:
                if not line.startswith(" "):
                    break
                include_paths.append(line[1:])
            if line.startswith("#include <"):
                collect = True
        return include_paths

    @property
    def compile_cmd(self) -> list[str]:
        return [
            "make",
            "-j",
            f"-C{self.source.parent}",
            f"DIM{self.target}_SWEEP_C={self.source.name}",
        ]

    def generate_code(self, alt_source=None, ephemeral=True):
        if alt_source:
            new_file = Path(alt_source).absolute()
        else:
            new_file = self.make_new_filename()
        self.scops.generate_code(self.source, Path(new_file))
        kwargs = {
            "source": new_file,
            "target": self.target,
            "compiler_options": self.user_compiler_options,
        }
        print(f"{new_file=}")
        return self.make_new_app(ephemeral, **kwargs)


snap = Snap(Path(__file__).parent / "SNAP/ports/snap-c/dim1_sweep.c", 1)

print(" ".join(snap.compile_cmd))

snap.generate_code()
