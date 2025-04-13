#!/usb/bin/env python

from pathlib import Path

from tadashi import TrEnum
from tadashi.apps import Simple


class MakefileApp(Simple):
    @property
    def compile_cmd(self) -> list[str]:
        cmd = ["make", f"-C{self.source.parent}", str(self.output_binary)]
        return cmd


def main():
    path = Path(__file__).parent / "fd3d_4.2.c"
    print(f"{path.exists()=}")
    app = MakefileApp(path)
    app.compile()
    orig_time = app.measure()
    print(f"{orig_time=}")
    nodes = app.scops[0].schedule_tree
    for i, node in enumerate(nodes):
        at = node.available_transformations
        if at and i < 10:
            print(f"{i}: {at}")
    node = nodes[7]
    tr = [TrEnum.FULL_SPLIT]
    node.transform(*tr)
    tapp = app.generate_code("foobar", ephemeral=False)
    print(f"{tapp.source=}")
    tapp.compile()
    new_time = tapp.measure()

    print(f"{orig_time=}")
    print(f"{new_time=}")
    speedup = orig_time / new_time
    print(f"{speedup=}")

    print("Done")


if __name__ == "__main__":
    main()
