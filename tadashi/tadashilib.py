#!/usr/bin/env python

import yaml

from core import *
from node import Node, get_node


def traverse(scop_idx, nodes, parent):
    node = get_node(scop_idx, parent)
    print(f"{node=}")
    parent_idx = len(nodes)
    nodes.append(node)
    if not node.is_leaf():
        for c in range(node.num_children):
            goto_child(scop_idx, c)
            node.children[c] = len(nodes)
            traverse(scop_idx, nodes, parent_idx)
            goto_parent(scop_idx)


def get_schedule_tree(scop_idx):
    nodes = []
    traverse(scop_idx, nodes, parent=-1)
    return nodes


def compare(sch_tree, sched):
    print("ok")


def main():
    # TODO: Emil double check if something usefull was done here and remove
    # scan_source(b"./examples/depnodep.c")
    num_scopes = get_num_scops(b"./examples/depnodep.c")
    print(f"{num_scopes=}")
    # child(0, 0)
    print(f"{get_num_children(0)=}")
    print(f"{get_dim_names(0)=}")
    schedules_trees = []
    for i in range(num_scopes):
        sched = get_schedule_yaml(i).decode()
        sched = yaml.load(sched, Loader=yaml.SafeLoader)
        sch_tree = get_schedule_tree(i)
        compare(sch_tree, sched)
        schedules_trees.append(sch_tree)
    free_scops()
    print("PYTHON DONE")


if __name__ == "__main__":
    main()
