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
    app = MakefileApp(path)
    tr = [[155, "interchange"], [122, "full_split"]]
    legals=app.scops[0].transform_list(tr)
    print(f"{legals=}")
    tapp = app.generate_code()
    print(f"{tapp.source=}")
    app.compile()
    tapp.compile()
    orig_time = app.measure()
    new_time = tapp.measure()
    print(f"{orig_time=}")
    print(f"{new_time=}")
    speedup = orig_time / new_time
    print(f"{speedup=}")

    print("Done")


if __name__ == "__main__":
    main()
