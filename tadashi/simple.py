#!/usr/bin/env python

from . import TRANSFORMATIONS, Scops, TrEnum
from .apps import Simple


def main():
    app = Simple("./examples/depnodep.c")
    scop = app.scops[0]  # select_scop()
    node = scop.schedule_tree[2]  # model.select_node(scop)
    print(f"{node=}")
    node.transform(TrEnum.TILE, 10)
    app = app.generate_code()
    app.compile()
    print(f"{app.output_binary=}")


if __name__ == "__main__":
    main()
