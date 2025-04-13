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
    for i, node in enumerate(app.scops[0].schedule_tree):
        at = node.available_transformations
        if at:
            print(f"{i}: {at}")

    print("Done")


if __name__ == "__main__":
    main()
