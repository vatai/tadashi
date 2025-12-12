#!/bin/env python
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from typing import Tuple

import cython
from cython.cimports.tadashi import isl, pet, transformations
from cython.cimports.tadashi.ccscop import ccScop

from .node_type import NodeType

SHOULD_NOT_HAPPEN = "This should not have happened. Please report an issue at https://github.com/vatai/tadashi/issues/"


class AstLoopType(Enum):
    """Possible values for `SET_LOOP_OPT`.

    `UNROLL` should be avoided unless the requirements in the
    `ISL Docs <https://libisl.sourceforge.io/user.html#AST-Generation-Options-Schedule-Tree>`_.
    are satisfied.

    """

    DEFAULT = 0
    ATOMIC = auto()
    UNROLL = auto()
    SEPARATE = auto()

    def __repr__(self):
        return f"TrEnum.{self.value.upper()}"


LowerUpperBound = namedtuple(
    "LowerUpperBound",
    ["lower", "upper"],
    defaults=[None, None],
)
"""Integer interval description.

Lower and upper bounds for describing (integer) intervals of valid
arguments for transformations. `None` indicates no upper/lower bound.

"""


_VALID = {}


def register(tre: TrEnum):
    """Register classes to _VALID dict."""

    def _decorator(cls):
        _VALID[tre] = cls
        return cls

    return _decorator


def _tilable(node: Node, dim: int) -> bool:  # todo: try to move to Node
    for _ in range(dim):
        if node.node_type != NodeType.BAND:
            return False
        # if "tile" in node.label and "outer" in node.label:
        #     return False
        node = node.children[0]
    return True


class Validation:
    @staticmethod
    def valid_tr(node: Node) -> bool:
        return True

    @staticmethod
    def valid_args(args: Tuple) -> bool:
        return True


class TrEnum(StrEnum):
    """Enums of implemented transformations.

    One of these enums needs to be passed to `Node.transform()` (with
    args) to perform the transformation.
    """

    TILE1D = auto()
    TILE2D = auto()
    TILE3D = auto()
    INTERCHANGE = auto()
    FULL_FUSE = auto()
    FUSE = auto()
    FULL_SPLIT = auto()
    SPLIT = auto()
    SCALE = auto()
    FULL_SHIFT_VAL = auto()
    PARTIAL_SHIFT_VAL = auto()
    FULL_SHIFT_VAR = auto()
    PARTIAL_SHIFT_VAR = auto()
    FULL_SHIFT_PARAM = auto()
    PARTIAL_SHIFT_PARAM = auto()
    SET_PARALLEL = auto()
    SET_LOOP_OPT = auto()


@register(TrEnum.TILE1D)
class Tile1DInfo:
    num_args = 1

    @staticmethod
    def valid(node: Node) -> bool:
        return _tilable(node, 1)

    @staticmethod
    def valid_args(node, size1) -> bool:
        return size1 > 1

    @staticmethod
    def available_args(node: Node):
        return [LowerUpperBound(lower=2, upper=None)]


@register(TrEnum.TILE2D)
class Tile2DInfo:
    num_args = 2

    @staticmethod
    def valid(node: Node) -> bool:
        return _tilable(node, 2)

    @staticmethod
    def valid_args(node, size1, size2):
        return size1 > 1 and size2 > 1

    @staticmethod
    def available_args(node: Node):
        return [
            LowerUpperBound(lower=2, upper=None),
            LowerUpperBound(lower=2, upper=None),
        ]


@register(TrEnum.TILE3D)
class Tile3DInfo:
    num_args = 3

    @staticmethod
    def valid(node: Node) -> bool:
        return _tilable(node, 3)

    @staticmethod
    def valid_args(node, size1, size2, size3):
        return size1 > 1 and size2 > 1 and size3 > 1

    @staticmethod
    def available_args(node: Node):
        return [
            LowerUpperBound(lower=2, upper=None),
            LowerUpperBound(lower=2, upper=None),
            LowerUpperBound(lower=2, upper=None),
        ]


@register(TrEnum.INTERCHANGE)
class ValidInterchange(Validation):
    num_args = 0

    @staticmethod
    def valid_tr(node: Node) -> bool:
        return (
            node.node_type == NodeType.BAND
            and len(node.children) == 1
            and node.children[0].node_type == NodeType.BAND
        )


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

    def __repr__(self):  # todo this is not a good node representation
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
    _type: cython.declare(isl.isl_schedule_node_type, visibility="public")
    num_children = cython.declare(int, visibility="public")
    parent_idx = cython.declare(int, visibility="public")
    index = cython.declare(int, visibility="public")
    label = cython.declare(str, visibility="public")
    location = cython.declare(list[int], visibility="public")
    loop_signature = cython.declare(str, visibility="public")
    expr = cython.declare(str, visibility="public")
    children_idx = cython.declare(list[str], visibility="public")

    def transform(self, tr: TrEnum, *args) -> cython.bint:
        """Execute the selected transformation.

        Args:
          TrEnum trkey: Transformation `Enum`.
          args: Arguments passed to the transformation corresponding toe `trkey`.
        """

        nargs = len(args)
        num = _VALID[tr].num_args
        if nargs != num:
            raise ValueError(f"Number of args ({nargs}) for {tr} should be {num}")
        if not _VALID[tr].valid_tr(self):
            raise ValueError(f"Transformation {tr} not valied here:\n{self.yaml_str}")
        _VALID[tr].valid_args(args)
        # self._check_args_valid(tr, args)
        # print(f"xxxxxx{self.yaml_str}")
        self.scop._locate(self.location)
        cur = self.scop.scop.current_node
        if tr == TrEnum.INTERCHANGE:
            cur = transformations.tadashi_interchange(cur)
        self.scop.scop.current_node = cur
        return True  # todo

        # tr_fun(self.scop.scop, *args)

        # TODO proc_args (from olden times)
        # tr = TRANSFORMATIONS[trkey]
        # if len(args) != len(tr.arg_help):
        #     raise ValueError(
        #         f"Incorrect number of args ({len(args)} should be {len(tr.arg_help)}) for {tr}!"
        #     )
        # if not tr.valid(self):
        #     msg = f"Not a valid transformation: {tr}"
        #     raise ValueError(msg)
        # if not tr.valid_args(self, *args):
        #     tr_name = tr.__class__.__name__
        #     msg = f"Not valid {args=}, for {tr_name=}"
        #     raise ValueError(msg)

        # func = getattr(ctadashi, tr.func_name)
        # self.scop.locate(self.location)
        # legal = func(self.scop.app_ptr, self.scop.scop_idx, *args)
        # return bool(legal)
        #######
        # template <typename Chk, typename Trn, typename... Args>
        # int
        # run_transform(Chk check_legality, Trn transform, Args &&...args) {
        #   if (this->tmp_node != nullptr)
        #     this->tmp_node = isl_schedule_node_free(this->tmp_node);
        #   tmp_node = isl_schedule_node_copy(this->current_node);
        #   this->tmp_legal = current_legal;

        #   current_node = transform(current_node, std::forward<Args>(args)...);
        #   isl_union_map *dep = isl_union_map_copy(this->dep_flow);
        #   current_legal = check_legality(current_node, dep);
        #   modified = true;
        #   return current_legal;
        # }
        pass

    @property
    def node_type(self) -> NodeType:
        return NodeType(self._type)

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
        node._type = node_type
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
