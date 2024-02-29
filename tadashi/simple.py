#!/usr/bin/env python

from apps import Simple
from tadashilib import Scops


def main():
    app = Simple("./examples/depnodep.c")
    scops = Scops(app)
    scop = scops[0]  # select_scop()
    node = scop.schedule_tree[2]  # model.select_node(scop)
    print(f"{node=}")
    node.tile(10)
    scops.generate_code()
    app.compile()
    print(f"{app.output_binary=}")
    pb_2mm_time = app.measure()
    print(f"{pb_2mm_time=}")


if __name__ == "__main__":
    main()
