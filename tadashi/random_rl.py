#!/usr/bin/env python

from apps import Polybench
from tadashilib import Scops

# import yaml


def main():
    app = Polybench(
        benchmark="linear-algebra/kernels/2mm",
        base="./deps/downloads/PolyBenchC-4.2.1-master/",
    )
    input_path = "./examples/depnodep.c"
    output_path = "./examples/depnodep.tadashilib.c"
    scops = Scops(app)
    schedules_trees = []
    for scop in scops:
        # sched = get_schedule_yaml(i).decode()
        # sched = yaml.load(sched, Loader=yaml.SafeLoader)
        sch_tree = scop.get_schedule_tree()
        # compare(sch_tree, sched)
        schedules_trees.append(sch_tree)

    scop = schedules_trees[0]  # select_scop()
    node = scop[5]  # model.select_node(scop)
    print(f"{node=}")
    # for each node, extract representation,
    # get score for how promising it looks to be transformed
    # select node to transform accroding to scores
    # transform the node
    # codegen new scops and measure performance
    node.tile(10)
    scops.generate_code()
    app.compile()
    print(f"{app.output_binary=}")
    pb_2mm_time = app.measure()
    print(f"{pb_2mm_time=}")


if __name__ == "__main__":
    main()
