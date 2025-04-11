#!/usr/bin/eval python
from pathlib import Path
from subprocess import DEVNULL, PIPE, run

from tadashi import TrEnum
from tadashi.apps import App, Simple


class Snap(App):
    def __init__(self, source: Path, target: int, compiler_options: list = None):
        msg = "Target should be 1 or 3 based on which filme source points to (dim1_sweep.c or dim3_sweep.c)"
        assert target in [1, 3], msg
        self.target = target
        include_path = self.mpi_include_paths()
        include_path += self.gcc_includes()
        source = self.preproc(source)
        print(f"{source=}")
        self._finalize_object(
            source,
            include_paths=include_path,
            compiler_options=compiler_options,
        )
        self.input_file = Path(__file__).parent / "snap_input_1"

    def preproc(self, source: Path):
        suffix = source.suffix
        pp_c_path = source.with_suffix(f".pp{suffix}")
        result = run(["mpicc", "-E", str(source)], stdout=PIPE, stderr=DEVNULL)
        with open(source, "r") as input_file:
            with open(pp_c_path, "w") as pp_c_file:
                for line in input_file:
                    if "#pragma scop" in line:
                        break
                    pp_c_file.write(line)
                pp_lines = result.stdout.decode().split("\n")
                for i, line in enumerate(pp_lines[0:]):
                    if "#pragma scop" in line:
                        break
                for i, line in enumerate(pp_lines[i:]):
                    pp_c_file.write(
                        line.replace("->", "___").replace(
                            "data_vars___vdelt[g-1]", "cond1"
                        )
                        + "\n"
                    )
                    if "#pragma endscop" in line:
                        break
                for line in input_file:
                    if "#pragma endscop" in line:
                        break
                for line in input_file:
                    pp_c_file.write(line)
        return pp_c_path

    @property
    def output_file(self):
        return Path(__file__).parent / f"{self.source}.out"

    def mpi_include_paths(self):
        result = run(["mpicc", "-compile_info"], stdout=PIPE)
        stdout = result.stdout.decode()
        opts = stdout.split()
        include_paths = [inc[2:] for inc in opts if inc.startswith("-I")]
        return include_paths

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
        cmd = [
            "make",
            "-j",
            f"-C{self.source.parent}",
            f"DIM{self.target}_SWEEP_C={self.source.name}",
            'A_PREFIX=""',
            f"A_SUFFIX={self.output_binary.name}",
        ]
        return cmd

    @property
    def run_cmd(self) -> list[str]:
        cmd = [
            "mpirun",
            "-n",
            "4",
            str(self.output_binary),
            "--fi",
            str(self.input_file),
            "--fo",
            str(self.output_file),
        ]
        return cmd

    def extract_runtime(self, stdout) -> list[str]:
        assert (
            stdout == "Success! Done in a SNAP!\n"
        ), "SNAP didn't crashed or something else went wrong"
        d = {}
        with open(self.output_file) as output_file:
            for line in output_file:
                if line.strip() == "Timing Summary":
                    break
            for line in output_file:
                if "." in line:
                    words = line.strip().split()
                    key = " ".join(words[:-1])
                    val = float(words[-1])
                    d[key] = val
        return d

    def generate_code(self, alt_source=None, ephemeral=True):
        if alt_source:
            new_file = self.source.parent / alt_source
        else:
            new_file = self.make_new_filename()
        print(f"{new_file}")
        self.scops.generate_code(self.source, Path(new_file))
        kwargs = {
            "source": new_file,
            "target": self.target,
            "compiler_options": self.user_compiler_options,
        }
        return self.make_new_app(ephemeral, **kwargs)

def smain():
    snap = Snap(Path(__file__).parent / "SNAP/ports/snap-c/dim1_sweep.c", 1)
    snap.compile()
    key = "Solve"
    base_time = snap.measure()[key]
    print(f"{base_time=}")
    node = snap.scops[0].schedule_tree[5] # simple
    tr = [TrEnum.FULL_SHIFT_VAL, 13]  # simple
    print(node.yaml_str)
    # print(f"{node.available_transformations=}")
    legal = node.transform(*tr)
    print(f">>> TR1: {legal=}")

    tapp = snap.generate_code("tile2d.c", ephemeral=False)
    tapp.compile()
    speedup = tapp.measure()[key] / base_time
    print(f"{speedup=}")

def main():
    snap = Snap(Path(__file__).parent / "SNAP/ports/snap-c/dim1_sweep.c", 1)
    snap.compile()
    key = "Solve"
    base_time = snap.measure()[key]
    print(f"{base_time=}")
    for ni, node in enumerate(snap.scops[0].schedule_tree):
        for ti, tr in enumerate(node.available_transformations):
            args = node.get_args(tr, -2, 2)[0]
            try:
                legal = node.transform(tr, *args)
                tapp = snap.generate_code(f"transformed{ni}-{ti}.c", ephemeral=False)
                tapp.compile()
                speedup = tapp.measure()[key] / base_time
                print(f">>> {speedup=}")
            except:
                print(f"EXCEPTION: {ni}-{ti}")

    return

def oldmain():
    splits_exist = True
    count = 0
    while splits_exist and count < 3:
        splits_exist = False
        for node_idx, node in enumerate(snap.scops[0].schedule_tree):
            available_transformations = node.available_transformations
            if available_transformations:
                print(f"{available_transformations=}")
                if TrEnum.FULL_SPLIT in available_transformations:
                    if node.transform(TrEnum.FULL_SPLIT):
                        # legal
                        print(f"[{node_idx}, FULL_SPLIT]")
                        app = snap.generate_code()
                        print(app.measure())
                        splits_exist = True
                        count += 1
                        break
                    else:
                        node.rollback()
    return
    for node_idx, node in enumerate(snap.scops[0].schedule_tree):
        available_transformations = node.available_transformations
        if available_transformations:
            print(f"(ii) {node_idx=}")
            print(f"(ii) {available_transformations=}")


if __name__ == "__main__":
    main()
