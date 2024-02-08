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
    print(f"PYTHON DONE")


if __name__ == "__main__":
    main()
