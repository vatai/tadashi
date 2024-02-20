#!/usr/bin/env python
import subprocess
from pathlib import Path

from node import Scops

# import yaml


def compare(sch_tree, sched):
    """Compare the schedule tree with the ISL traversal in C."""
    print("ok")
    raise NotImplemented()


class App:
    def compile(self):
        pass


class Polybench(App):
    def __init__(self, name):
        self.name = name
        while str(self.include_dir).startswith("apple"):
            self.include_dir = self.include_dir.parents
        self.include_dir = Path(name).parent

    def compile(self):
        cmd = ["gcc", self.name, "-I", str(self.include_dir)]
        print(" ".join(cmd))
        subprocess.run(cmd)


def main():
    pb_2mm = Polybench("./deps/polybench-c-3.2/linear-algebra/kernels/2mm/2mm.c")
    pb_2mm.compile()
    input_path = "./examples/depnodep.c"
    output_path = "./examples/depnodep.tadashilib.c"
    scops = Scops(input_path)
    schedules_trees = []
    for scop in scops:
        # sched = get_schedule_yaml(i).decode()
        # sched = yaml.load(sched, Loader=yaml.SafeLoader)
        sch_tree = scop.get_schedule_tree()
        # compare(sch_tree, sched)
        schedules_trees.append(sch_tree)

    scop = schedules_trees[0]  # select_scop()
    node = scop[1]  # model.select_node(scop)
    print(f"{node=}")
    # for each node, extract representation,
    # get score for how promising it looks to be transformed
    # select node to transform accroding to scores
    # transform the node
    # codegen new scops and measure performance
    node.tile(10)
    scops.generate_code(output_path)
    print(f"PYTHON DONE")


if __name__ == "__main__":
    main()
