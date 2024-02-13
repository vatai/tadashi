#!/usr/bin/env python

# import yaml

from node import Scops


def compare(sch_tree, sched):
    print("ok")


def main():
    scops = Scops(b"./examples/depnodep.c")
    schedules_trees = []
    for scop in scops:
        # sched = get_schedule_yaml(i).decode()
        # sched = yaml.load(sched, Loader=yaml.SafeLoader)
        sch_tree = scop.get_schedule_tree()
        # compare(sch_tree, sched)
        schedules_trees.append(sch_tree)

    scop = schedules_trees[0]  # select_scop()
    node = scop[0]  # model.select_node(scop)
    print(f"{node=}")
    print(f"{schedules_trees[0][1].locate()=}")
    # tr = node.select_transform()
    # tr.do()
    print(f"PYTHON DONE")


if __name__ == "__main__":
    main()
