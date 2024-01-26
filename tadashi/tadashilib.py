#!/usr/bin/env python

import yaml

from core import *


def get_node(scop_idx, parent):
    num_children = get_num_children(scop_idx)
    inner_dim_names = get_dim_names(scop_idx).decode().split(";")[:-1]
    dim_names = [t.split("|")[:-1] for t in inner_dim_names]
    node = Node(
        node_type=get_type(scop_idx),
        type_str=get_type_str(scop_idx),
        num_children=num_children,
        parent=parent,
        dim_names=dim_names,
        expr=get_expr(scop_idx),
    )
    return node


class Node:
    def __init__(
        self,
        node_type,
        type_str,
        num_children,
        parent,
        dim_names,
        expr,
    ) -> None:
        self.node_type = node_type
        self.type_str = type_str
        self.num_children = num_children
        self.parent = parent
        self.dim_names = dim_names
        self.expr = expr
        self.children = [-1 for _ in range(num_children)]

    def __repr__(self):
        return f"Node type: {self.type_str}, {self.dim_names}, {self.expr}"

    def is_leaf(self):
        return self.node_type == 6


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
