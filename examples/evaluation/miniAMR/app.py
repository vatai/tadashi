#!/usr/bin/env python
import re
from pathlib import Path
from subprocess import DEVNULL, PIPE, run
from typing import Optional

from colorama import Fore as CF
from tadashi import TrEnum
from tadashi.apps import App
from tadashi.translators import Translator

BASE_PATH = Path(__file__).parent / "miniAMR/ref"


class miniAMR(App):
    base: Path

    def __init__(
        self,
        num_ranks: int,
        run_args: Optional[list[str]] = None,
        base: Path = BASE_PATH,
        *,
        source: Path = BASE_PATH / "stencil.c",
        translator: Optional[Translator] = None,
        compiler_options: list = None,
        ephemeral: bool = False,
        populate_scops: bool = True,
    ):
        self.base = base
        self.num_ranks = num_ranks
        if not run_args:
            run_args = []
        self.run_args = run_args
        # todo, move this to amend_compiler_options
        include_paths = (
            self._mpich_includes()
            + self._gcc_includes("gcc")
            + self._gcc_includes("mpicc")
        )
        super().__init__(
            source=source,
            translator=translator,
            compiler_options=compiler_options,
            ephemeral=ephemeral,
            populate_scops=populate_scops,
        )

    @staticmethod
    def _mpich_includes():
        cmd = ["mpicc", "-compile_info"]
        result = run(cmd, stdout=PIPE, stderr=DEVNULL, check=False)
        if result.returncode == 1:
            return []
        stdout = result.stdout.decode()
        opts = stdout.split()
        include_paths = [inc[2:] for inc in opts if inc.startswith("-I")]
        return include_paths

    @staticmethod
    def _gcc_includes(compiler):
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

    def codegen_init_args(self):
        return {
            "num_ranks": self.num_ranks,
            "base": self.base,
            "run_args": self.run_args,
        }

    def compile_cmd(self) -> list[str]:
        cmd = [
            "make",
            "-j",
            f"-C{self.source.parent}",
            f"STENCIL={self.source.with_suffix('').name}",
            f"EXEC={self.output_binary.name}",
        ]
        return cmd

    def run_cmd(self) -> list[str]:
        cmd = [
            "mpirun",
            "-N",
            str(self.num_ranks),
            str(self.output_binary),
            "--stencil",
            "0",
            *self.run_args,
        ]
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
    app.scops[scop_idx].transform_list(tr)
    print(f"{app.legal=}")
    if not app.legal:
        return
    for i, node in enumerate(app.scops[scop_idx].schedule_tree):
        at = node.available_transformations
        if at:
            print(f"{i} {at}")
    # return

    repeat = 10
    app.compile()
    orig_time = app.measure(repeat)
    for ts in [61]:
        # tr = [
        #        [16, TrEnum.FULL_SPLIT],
        #        [20, TrEnum.INTERCHANGE],
        #        [15, TrEnum.FULL_FUSE],
        #        [11, TrEnum.FULL_SPLIT],
        #        [10, TrEnum.FULL_FUSE],
        #        [6, TrEnum.FULL_SPLIT],
        #        ]
        app.scops[scop_idx].reset()
        app.scops[scop_idx].transform_list(tr)
        print(f"{app.legal=}")
        if not app.legal:
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
