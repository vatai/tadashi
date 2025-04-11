#!/usr/bin/env python

from pathlib import Path

from tadashi.apps import App

BASE_PATH = Path(__file__).parent / "miniAMR/ref"


class miniAMR(App):
    def __init__(self, base: Path = BASE_PATH, compiler_options: list = None):
        self.base = base
        self._finalize_object(
            source=Path(f"{base}/stencil.c"),
            include_paths=[],
            compiler_options=compiler_options,
        )

    @property
    def compile_cmd(self) -> list[str]:
        cmd = [
            "make",
            "-j",
            f"-C{self.source.parent}",
            f"STENCIL={self.source.with_suffix('').name}",
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


def main():
    app = miniAMR()
    node = app.scops[0].schedule_tree[0]
    print(node.yaml_str)
    print(f"{app.source=}")
    print("done")


if __name__ == "__main__":
    main()
