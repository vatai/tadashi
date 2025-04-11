#!/usr/bin/env python
import re
from pathlib import Path

from colorama import Fore as CF
from tadashi import TrEnum
from tadashi.apps import App

BASE_PATH = Path(__file__).parent / "miniAMR/ref"


class miniAMR(App):
    def __init__(
        self,
        source: Path = BASE_PATH / "stencil.c",
        base: Path = BASE_PATH,
        run_args: list[str] = None,
        compiler_options: list = None,
    ):
        self.base = base
        if not run_args:
            run_args = []
        self.run_args = run_args
        self._finalize_object(
            source=source,
            include_paths=[],
            compiler_options=compiler_options,
        )

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
        cmd = [str(self.output_binary), *self.run_args]
        return cmd

    def extract_runtime(self, stdout: str) -> float:
        lines = stdout.split("\n")
        for line in lines:
            if line.startswith("Summary:"):
                match = re.match(r".*time (\d+.\d+).*", line)
                return float(match.groups()[0])
        raise Exception("No output found")


def main():
    app = miniAMR()
    app.compile()
    orig_time = app.measure()

    node = app.scops[0].schedule_tree[0]
    # print(node.yaml_str)
    for i, node in enumerate(app.scops[0].schedule_tree):
        at = node.available_transformations
        if at and False:
            print(f"{CF.RED}{i}{CF.RESET} {at}")
    node = app.scops[0].schedule_tree[6]
    tr = [TrEnum.FULL_SPLIT]
    legal = node.transform(*tr)
    print(f"{legal=}")

    tapp = app.generate_code("foobar.c", ephemeral=False)
    tapp.compile()
    tr_time = tapp.measure()
    speedup = orig_time / tr_time
    print(f"{orig_time=}")
    print(f"{tr_time=}")
    print(f"{speedup=}")

    print("done")


if __name__ == "__main__":
    main()
