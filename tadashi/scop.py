#!/bin/env python


import cython
from cython.cimports.tadashi import isl, pet
from cython.cimports.tadashi.ccscop import ccScop
from cython.cimports.tadashi.transformations import *

from .node import Node
from .node_type import NodeType


@cython.cclass
class Scop:
    scop: cython.pointer(ccScop)

    @staticmethod
    @cython.cfunc
    def create(ptr: cython.pointer(ccScop)) -> Scop:
        scop = Scop()
        scop.scop = ptr
        return scop

    def __repr__(self):
        node = self.scop.current_node
        return isl.isl_schedule_node_to_str(node).decode()

    def get_label(self):
        pass  # todo

    def get_loop_signature(self):
        pass  # todo

    def get_expr(self):
        pass  # todo

    def _make_node(self, parent, current_idx, location):

        cur = self.scop.current_node
        num_children = isl.isl_schedule_node_n_children(cur)
        node = Node(
            scop=self,
            node_type=NodeType(isl.isl_schedule_node_get_type(cur)),
            num_children=num_children,
            parent_idx=parent,
            index=current_idx,
            label=self.get_label(),
            location=location,
            loop_signature=self.get_loop_signature(),
            expr=self.get_expr(),
            children_idx=[-1] * num_children,
        )
        return node

    def goto_root(self) -> None:
        ptr = self.scop.current_node
        ptr = isl.isl_schedule_node_root(ptr)
        self.scop.current_node = ptr

    def goto_parent(self) -> None:
        ptr = self.scop.current_node
        ptr = isl.isl_schedule_node_parent(ptr)
        self.scop.current_node = ptr

    def goto_child(self, n: int) -> None:
        ptr = self.scop.current_node
        ptr = isl.isl_schedule_node_child(ptr, n)
        self.scop.current_node = ptr

    def _traverse(self, nodes: list[Node], parent: int, location: list[int]):
        current_idx = len(nodes)
        node = self._make_node(parent, current_idx, location)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                self.goto_child(c)
                node.children_idx[c] = len(nodes)
                self._traverse(nodes, current_idx, location + [c])
                self.goto_parent()

    @property
    def schedule_tree(self) -> list[Node]:
        self.goto_root()
        nodes: list[Node] = []
        self._traverse(nodes, parent=-1, location=[])
        return nodes

    def foobar_transform(self, node_idx: int):  # TODO
        node = self.scop.current_node
        node = isl.isl_schedule_node_first_child(node)
        node = tadashi_interchange(node)
        result = isl.isl_schedule_node_to_str(node).decode()
        self.scop.current_node = node
        return result
