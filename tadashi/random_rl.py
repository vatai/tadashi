#!/usr/bin/env python

from apps import Polybench
from tadashilib import Scops, Transformation


def main():
    app = Polybench(
        benchmark="linear-algebra/kernels/2mm",
        base="build/_deps/polybench-src/",
    )
    scops = Scops(app)
    scop = scops[0]  # select_scop()
    node = scop.schedule_tree[5]  # model.select_node(scop)
    # print(f"{node=}")
    # for each node, extract representation,
    # get score for how promising it looks to be transformed
    # select node to transform accroding to scores
    # transform the node
    # codegen new scops and measure performance
    print(f"{node.avaliable_transformation=}")
    # node.transform(Transformation.TILE, 10)
    node.transform(Transformation.PARTIAL_SHIFT_ID, 0, 0)
    scops.generate_code()
    app.compile()
    print(f"{app.output_binary=}")
    # app_time = app.measure()
    # print(f"{app_time=}")


if __name__ == "__main__":
    main()
