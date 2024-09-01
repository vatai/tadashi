#!/usr/bin/env python

from .apps import Polybench, Simple
from .tadashilib import Scops, TrEnum


def main():
    app = Polybench(
        benchmark="linear-algebra/kernels/2mm",
        base="build/_deps/polybench-src/",
    )
    node_idx = 5
    # app = Simple(source="examples/depnodep-stripped.c")
    app = Simple(source="examples/threeloop.c")
    node_idx = 1
    scops = Scops(app)
    scop = scops[0]  # select_scop()
    node = scop.schedule_tree[node_idx]  # model.select_node(scop)
    # print(f"{node=}")
    # for each node, extract representation,
    # get score for how promising it looks to be transformed
    # select node to transform accroding to scores
    # transform the node
    # codegen new scops and measure performance
    print(f"{node.avaliable_transformation=}")
    # node.transform(Transformation.TILE, 10)
    node.transform(TrEnum.PARTIAL_SHIFT_VAL, 0, 42)
    scops.generate_code()
    # app.compile()
    # print(f"{app.output_binary=}")
    # app_time = app.measure()
    # print(f"{app_time=}")


if __name__ == "__main__":
    main()
