#!/usr/bin/env python

from .apps import Simple
from .tadashilib import TRANSFORMATIONS, Scops, TrEnum


def main():
    app = Simple("./examples/depnodep.c")
    scops = Scops(app)
    scop = scops[0]  # select_scop()
    node = scop.schedule_tree[2]  # model.select_node(scop)
    print(f"{node=}")
    node.transform(TrEnum.TILE, 10)
    scops.generate_code()
    app.compile()
    print(f"{app.output_binary=}")


if __name__ == "__main__":
    main()
