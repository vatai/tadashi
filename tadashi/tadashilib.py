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
    def __init__(self, name, base):
        self.benchmark = Path(name)
        self.base = Path(base)

    def compile(self):
        compiler_opts_path = self.base / self.benchmark / "compiler.opts"
        compiler_opts = compiler_opts_path.read_text().split()
        cmd = [
            "gcc",
            self.base / self.benchmark / (str(self.benchmark.name) + ".c"),
            self.base / "utilities/polybench.c",
            "-I",
            self.base / "utilities",
            *compiler_opts,
        ]
        compiled_cmd = " ".join(map(str, cmd))
        print(f"{compiled_cmd=}")
        subprocess.run(cmd)


def main():
    pb_2mm = Polybench(
        name="linear-algebra/kernels/2mm",
        base="./deps/downloads/polybench-c-3.2",
    )
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
