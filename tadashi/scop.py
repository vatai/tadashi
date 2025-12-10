#!/bin/env python

from dataclasses import dataclass

import cython
from cython.cimports.tadashi import isl, pet, transformations
from cython.cimports.tadashi.ccscop import ccScop

from . import SHOULD_NOT_HAPPEN
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

    @property
    def schedule_tree(self) -> list[Node]:
        self._goto_root()
        nodes: list[Node] = []
        self._traverse(nodes, parent=-1, location=[])
        return nodes

    def __repr__(self):
        node = self.scop.current_node
        return isl.isl_schedule_node_to_str(node).decode()

    @cython.cfunc
    def _cur(self) -> isl.schedule_node:
        # shortcut to save typing
        return self.scop.current_node

    def _node_type_is(self, node_type: NodeType):
        tmp = isl.isl_schedule_node_get_type(self._cur())
        return NodeType(tmp) == node_type

    def _get_label(self):
        if not self._node_type_is(NodeType.BAND):
            return ""
        mupa = isl.isl_schedule_node_band_get_partial_schedule(self._cur())
        label = isl.isl_multi_union_pw_aff_get_tuple_name(mupa, isl.isl_dim_out)
        mupa = isl.isl_multi_union_pw_aff_free(mupa)
        return label.decode()

    def _get_loop_signature(self):
        # Scop *si = app->scops[scop_idx];
        if not self._node_type_is(NodeType.BAND):
            return "[]"
        mupa = isl.isl_schedule_node_band_get_partial_schedule(self._cur())
        out_dims = isl.isl_multi_union_pw_aff_dim(mupa, isl.isl_dim_out)
        assert out_dims == 1, SHOULD_NOT_HAPPEN
        # TODO save name??? Comment copied from `times of old'(tm)
        domain = isl.isl_multi_union_pw_aff_domain(mupa)
        num_sets = isl.isl_union_set_n_set(domain)
        slist = isl.isl_union_set_get_set_list(domain)
        result = "["
        for set_idx in range(num_sets):
            if set_idx:
                result += ", "
            set = isl.isl_set_list_get_at(slist, set_idx)
            num_params = isl.isl_set_dim(set, isl.isl_dim_param)
            result += "{'params': ["
            for di in range(num_params):
                if di:
                    result += ", "
                dim_name = isl.isl_set_get_dim_name(set, isl.isl_dim_param, di)
                result += f"'{dim_name.decode()}'"
            result += "], 'vars': ["
            num_vars = isl.isl_set_dim(set, isl.isl_dim_set)
            for di in range(num_vars):
                if di:
                    result += ", "
                dim_name = isl.isl_set_get_dim_name(set, isl.isl_dim_set, di)
                result += f"'{dim_name.decode()}'"
            result += "]}"
            isl.isl_set_free(set)
        result += "]"
        isl.isl_set_list_free(slist)
        isl.isl_union_set_free(domain)
        return result

    def _get_expr(self) -> str:
        if not self._node_type_is(NodeType.BAND):
            return ""
        cur = self.scop.current_node
        mupa = isl.isl_schedule_node_band_get_partial_schedule(cur)
        expr = isl.isl_multi_union_pw_aff_to_str(mupa)
        mupa = isl.isl_multi_union_pw_aff_free(mupa)
        return expr.decode()

    def _goto_root(self) -> None:
        ptr = self.scop.current_node
        ptr = isl.isl_schedule_node_root(ptr)
        self.scop.current_node = ptr

    def _goto_parent(self) -> None:
        ptr = self.scop.current_node
        ptr = isl.isl_schedule_node_parent(ptr)
        self.scop.current_node = ptr

    def _goto_child(self, n: int) -> None:
        ptr = self.scop.current_node
        ptr = isl.isl_schedule_node_child(ptr, n)
        self.scop.current_node = ptr

    def _locate(self, loc: list[int]) -> None:
        self._goto_root()
        for child in loc:
            print(f"loc(): {child=}")
            print(isl.isl_schedule_node_to_str(self._cur()).decode())
            self._goto_child(child)

    def _yaml_str(self) -> str:
        node = self.scop.current_node
        return isl.isl_schedule_node_to_str(node).decode()

    def _traverse(self, nodes: list[Node], parent: int, location: list[int]):
        current_idx = len(nodes)
        node = Node.create(self.scop, parent, current_idx, location)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                self._goto_child(c)
                node.children_idx[c] = len(nodes)
                self._traverse(nodes, current_idx, location + [c])
                self._goto_parent()


@cython.cclass
class Node:
    """Schedule node (Python representation)."""

    scop: Scop
    node_type: NodeType
    num_children = cython.declare(int, visibility="public")
    parent_idx = cython.declare(int, visibility="public")
    index = cython.declare(int, visibility="public")
    label = cython.declare(str, visibility="public")
    location = cython.declare(list[int], visibility="public")
    loop_signature = cython.declare(str, visibility="public")
    expr = cython.declare(str, visibility="public")
    children_idx = cython.declare(list[str], visibility="public")

    @staticmethod
    @cython.cfunc
    def create(
        ptr: cython.pointer(ccScop),
        parent: int,
        current_idx: int,
        location: list[int],
    ) -> Node:
        num_children = isl.isl_schedule_node_n_children(ptr.current_node)
        node_type = isl.isl_schedule_node_get_type(ptr.current_node)
        node = Node()
        scop = Scop.create(ptr)
        node.scop = scop
        node.node_type = NodeType(node_type)
        node.num_children = num_children
        node.parent_idx = parent
        node.index = current_idx
        node.label = scop._get_label()
        node.location = location
        node.loop_signature = scop._get_loop_signature()
        node.expr = scop._get_expr()
        node.children_idx = [-1] * num_children
        return node

    @property
    def parent(self):
        """The node which is the parent of the current node."""
        return self.scop.schedule_tree[self.parent_idx]

    @property
    def children(self):
        """List of nodes which are the children of the current node."""
        return [self.scop.schedule_tree[i] for i in self.children_idx]

    @property
    def yaml_str(self):
        self.scop._locate(self.location)
        return self.scop._yaml_str()

    def __repr__(self):
        """Textual representation of a node."""
        words = [
            "Node type:",
            f"{self.node_type},",
            f"{self.loop_signature},",
            f"{self.expr},",
            f"{self.location}",
        ]
        return " ".join(words)

    def transform(self: "TrEnum", *args) -> bool:
        pass
