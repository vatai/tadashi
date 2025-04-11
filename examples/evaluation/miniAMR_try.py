#!/usr/bin/env python
from pathlib import Path

import colorama
from tadashi import TrEnum
from tadashi.apps import Simple


def main():
    color_red = colorama.Fore.LIGHTRED_EX
    color_reset = colorama.Fore.RESET
    path = Path(__file__).parent.parent / "ecp-apps/miniAMR/openmp/stencil.c"
    print(path.exists())
    app = Simple(path)
    print(app)
    print(len(app.scops))
    node = app.scops[0].schedule_tree[0]
    # print(node.yaml_str)
    for i, node in enumerate(app.scops[0].schedule_tree):
        if node.available_transformations:
            print(f"{color_red}{i}{color_reset}: {node.available_transformations}")
    node = app.scops[0].schedule_tree[6]
    tr = [TrEnum.FULL_SPLIT]
    legal = node.transform(*tr)
    print(f"{legal=}")
    tapp = app.generate_code("foobar.c", ephemeral=False)
    print(tapp.source)
    print("DONE")


if __name__ == "__main__":
    main()
