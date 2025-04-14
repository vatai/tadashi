#!/usr/bin/env python
import re
from pathlib import Path
from subprocess import DEVNULL, PIPE, run
from typing import Optional

from colorama import Fore as CF
from tadashi import TrEnum
from tadashi.apps import App

BASE_PATH = Path(__file__).parent / "miniAMR/ref"


class miniAMR(App):
    base: Path

    def __init__(
        self,
        num_ranks: int,
        source: Path = BASE_PATH / "stencil.c",
        run_args: Optional[list[str]] = None,
        compiler_options: list = None,
        base: Path = BASE_PATH,
    ):
        self.base = base
        self.num_ranks = num_ranks
        if not run_args:
            run_args = []
        self.run_args = run_args
        include_paths = (
            self.mpich_includes()
            + self.gcc_includes("gcc")
            + self.gcc_includes("mpicc")
        )
        self._finalize_object(
            source=source,
            include_paths=include_paths,
            compiler_options=compiler_options,
        )

    @staticmethod
    def mpich_includes():
        cmd = ["mpicc", "-compile_info"]
        result = run(cmd, stdout=PIPE, stderr=DEVNULL, check=False)
        if result.returncode == 1:
            return []
        stdout = result.stdout.decode()
        opts = stdout.split()
        include_paths = [inc[2:] for inc in opts if inc.startswith("-I")]
        return include_paths

    @staticmethod
    def gcc_includes(compiler):
        cmd = [compiler, "-xc", "-E", "-v", "/dev/null"]
        result = run(cmd, stdout=DEVNULL, stderr=PIPE, check=False)
        if result.returncode == 1:
            return []
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

    def generate_code(self, alt_source: str = None, ephemeral=True):
        if alt_source:
            assert str(alt_source).endswith(".c")
            assert Path(alt_source).name == str(alt_source)
            new_file = self.source.parent / alt_source
        else:
            new_file = self.make_new_filename()
        self.scops.generate_code(self.source, Path(new_file))
        kwargs = {
            "source": new_file,
            "base": self.base,
            "num_ranks": self.num_ranks,
            "run_args": self.run_args,
        }
        return self.make_new_app(ephemeral, **kwargs)

    @property
    def compile_cmd(self) -> list[str]:
        cmd = [
            "make",
            "-j",
            f"-C{self.source.parent}",
            f"STENCIL={self.source.with_suffix('').name}",
            f"EXEC={self.output_binary.name}",
        ]
        return cmd

    @property
    def run_cmd(self) -> list[str]:
        cmd = ["mpirun", "-N", str(self.num_ranks), str(self.output_binary), "--stencil", "0", *self.run_args,]
        return cmd

    def extract_runtime(self, stdout: str) -> float:
        lines = stdout.split("\n")
        # scop_idx_check = set([])
        for line in lines:
            # if line.startswith("@@@") and scop_idx_check != line:
            #     scop_idx_check.add(line)
            if line.startswith("Summary:"):
                match = re.match(r".*time (\d+.\d+).*", line)
                # print(f"{scop_idx_check=}")
                return float(match.groups()[0])
        raise Exception("No output found")


def main():
    scop_idx = 0
    app = miniAMR(
        num_ranks=6,
        run_args=["--nx", "10", "--ny", "10", "--nz", "82", "--npz", "3", "--npx", "2"],
        # run_args=["--nx", "10", "--ny", "10", "--nz", "80", "--npz", "3", "--npx", "2"],
    )

    # node = app.scops[scop_idx].schedule_tree[0]
    # print(node.yaml_str)

    node = app.scops[scop_idx].schedule_tree[16]
    tr = [
                [16, TrEnum.FULL_SPLIT],
                [20, TrEnum.INTERCHANGE],
                [15, TrEnum.FULL_FUSE],
                [11, TrEnum.FULL_SPLIT],
                [10, TrEnum.FULL_FUSE],
                [6, TrEnum.FULL_SPLIT],
                [17, TrEnum.FULL_SPLIT],
                # [5, TrEnum.FULL_FUSE],
            ]
    legals = app.scops[scop_idx].transform_list(tr)
    print(f"{legals=}")
    if not all(legals):
        return
    for i, node in enumerate(app.scops[scop_idx].schedule_tree):
        at = node.available_transformations
        if at:
            print(f"{i} {at}")
    # return

    repeat=10
    app.compile()
    orig_time = app.measure(repeat)
    for ts in [61]:
        #tr = [
        #        [16, TrEnum.FULL_SPLIT],
        #        [20, TrEnum.INTERCHANGE],
        #        [15, TrEnum.FULL_FUSE],
        #        [11, TrEnum.FULL_SPLIT],
        #        [10, TrEnum.FULL_FUSE],
        #        [6, TrEnum.FULL_SPLIT],
        #        ]
        app.scops[scop_idx].reset()
        legals = app.scops[scop_idx].transform_list(tr)
        print(f"{legals=}")
        if not all(legals):
            continue
        tapp = app.generate_code(f"{ts=}.c", ephemeral=False)
        tapp.compile()
        tr_time = tapp.measure(repeat)
        speedup = orig_time / tr_time
        print(f"{ts=}")
        print(f"{orig_time=}")
        print(f"{tr_time=}")
        print(f"{speedup=}")

    print("done")


if __name__ == "__main__":
    main()
