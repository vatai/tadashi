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
        # if (isl_schedule_node_get_type(si->current_node) != isl_schedule_node_band)
        #   return "[]";
        # std::stringstream ss;
        # isl_multi_union_pw_aff *mupa;
        # mupa = isl_schedule_node_band_get_partial_schedule(si->current_node);
        # // assert(isl_multi_union_pw_aff_dim(mupa, isl_dim_out) == 1);
        # // TODO save name
        # isl_union_set *domain = isl_multi_union_pw_aff_domain(mupa);
        # isl_size num_sets = isl_union_set_n_set(domain);
        # isl_set_list *slist = isl_union_set_get_set_list(domain);
        # ss << "[";
        # for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
        #   if (set_idx)
        #     ss << ", ";
        #   isl_set *set = isl_set_list_get_at(slist, set_idx);
        #   isl_size num_params = isl_set_dim(set, isl_dim_param);
        #   ss << "{'params' : [";
        #   for (isl_size di = 0; di < num_params; di++) {
        #     if (di)
        #       ss << ", ";
        #     ss << "'" << isl_set_get_dim_name(set, isl_dim_param, di) << "'";
        #   }
        #   ss << "], 'vars' :[";
        #   isl_size num_vars = isl_set_dim(set, isl_dim_set);
        #   for (isl_size di = 0; di < num_vars; di++) {
        #     if (di)
        #       ss << ", ";
        #     ss << "'" << isl_set_get_dim_name(set, isl_dim_set, di) << "'";
        #   }
        #   ss << "]}";
        #   isl_set_free(set);
        # }
        # ss << "]";
        # isl_set_list_free(slist);
        # isl_union_set_free(domain);
        # return si->add_string(ss);
        pass  # todo

    def _get_expr(self) -> str:
        if not self._node_type_is(NodeType.BAND):
            return ""
        cur = self.scop.current_node
        mupa = isl.isl_schedule_node_band_get_partial_schedule(cur)
        expr = isl.isl_multi_union_pw_aff_to_str(mupa)
        mupa = isl.isl_multi_union_pw_aff_free(mupa)
        return expr.decode()

    def _make_node(self, parent, current_idx, location):
        num_children = isl.isl_schedule_node_n_children(self._cur())
        node_type = isl.isl_schedule_node_get_type(self._cur())
        node = Node(
            scop=self,
            node_type=NodeType(node_type),
            num_children=num_children,
            parent_idx=parent,
            index=current_idx,
            label=self._get_label(),
            location=location,
            loop_signature=self._get_loop_signature(),
            expr=self._get_expr(),
            children_idx=[-1] * num_children,
        )
        return node

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

    def _traverse(self, nodes: list[Node], parent: int, location: list[int]):
        current_idx = len(nodes)
        node = self._make_node(parent, current_idx, location)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                self._goto_child(c)
                node.children_idx[c] = len(nodes)
                self._traverse(nodes, current_idx, location + [c])
                self._goto_parent()

    def foobar_transform(self, node_idx: int):  # TODO
        node = self.scop.current_node
        node = isl.isl_schedule_node_first_child(node)
        node = tadashi_interchange(node)
        result = isl.isl_schedule_node_to_str(node).decode()
        self.scop.current_node = node
        return result
