#!/usr/bin/env python

import yaml

from core import free_scops, get_num_scops
from node import Node, Scop


def compare(sch_tree, sched):
    print("ok")


def main():
    # TODO: Emil double check if something usefull was done here and remove
    # scan_source(b"./examples/depnodep.c")
    scops = [Scop(i) for i in range(get_num_scops(b"./examples/depnodep.c"))]
    # print(f"{num_scopes=}")
    # child(0, 0)
    schedules_trees = []
    for scop in scops:
        # sched = get_schedule_yaml(i).decode()
        # sched = yaml.load(sched, Loader=yaml.SafeLoader)
        sch_tree = scop.get_schedule_tree()
        # compare(sch_tree, sched)
        schedules_trees.append(sch_tree)
    free_scops()
    print("PYTHON DONE")


if __name__ == "__main__":
    main()
