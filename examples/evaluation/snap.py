#!/usr/bin/eval python
from pathlib import Path
from subprocess import DEVNULL, PIPE, run

from tadashi import TrEnum
from tadashi.apps import App, Simple


class Snap(App):
    def __init__(self, source, target, compiler_options=[]):
        msg = "Target should be 1 or 3 based on which filme source points to (dim1_sweep.c or dim3_sweep.c)"
        assert target in [1, 3], msg
        self.target = target
        include_path = self.mpi_include_paths()
        include_path += self.gcc_includes()
        self._finalize_object(
            source,
            include_paths=include_path,
            compiler_options=compiler_options,
        )

    def mpi_include_paths(self):
        result = run(["mpicc", "-compile_info"], stdout=PIPE)
        stdout = result.stdout.decode()
        opts = stdout.split()
        return [inc[2:] for inc in opts if inc.startswith("-I")]

    def gcc_includes(self):
        cmd = ["gcc", "-xc", "-E", "-v", "/dev/null"]
        result = run(cmd, stdout=DEVNULL, stderr=PIPE)
        stderr = result.stderr.decode()
        include_paths = []
        collect = False
        for line in stderr.split("\n"):
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
        return self.make_new_app(ephemeral, **kwargs)


# snap = Simple(Path(__file__).parent / "SNAP/ports/snap-c/dim1_sweep.c", 1)
snap = Snap(Path(__file__).parent / "SNAP/ports/snap-c/dim1_sweep.c", 1)
splits_exist = True
while splits_exist:
    splits_exist = False
    for node_idx, node in enumerate(snap.scops[0].schedule_tree):
        available_transformations = node.available_transformations
        if available_transformations:
            print(f"{node_idx=}")
            print(f"{available_transformations=}")
            if TrEnum.FULL_SPLIT in available_transformations:
                print(f"{node_idx=}")
                node.transform(TrEnum.FULL_SPLIT)
                splits_exist = True


for node_idx, node in enumerate(snap.scops[0].schedule_tree):
    available_transformations = node.available_transformations
    if available_transformations:
        print(f"(ii) {node_idx=}")
        print(f"(ii) {available_transformations=}")

# print(" ".join(snap.compile_cmd))

# snap.generate_code()
