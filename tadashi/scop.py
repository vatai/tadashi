#!/bin/env python
import multiprocessing
import re
from ast import literal_eval
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from typing import Tuple

import cython
from cython.cimports.tadashi import isl, pet, transformations
from cython.cimports.tadashi.ccscop import ccScop

from . import _tr_wrappers as w
from .node_type import NodeType

SHOULD_NOT_HAPPEN = "This should not have happened. Please report an issue at https://github.com/vatai/tadashi/issues/"
DELETED_TRANSLATOR_EXCMSG = (
    "Something is wrong! Was the translator deleted before the scop?"
)


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


CAMEL_TO_SNAKE = re.compile(r"(?<=[a-z])(?=[A-Z0-9])")


class TrEnum(StrEnum):
    """Enums of implemented transformations.

    One of these enums needs to be passed to `Node.transform()` (with
    args) to perform the transformation.
    """

    TILE_1D = auto()
    TILE_2D = auto()
    TILE_3D = auto()
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


@cython.cclass
class Node:
    """Schedule node (Python representation)."""

    scop: Scop
    _type = cython.declare(isl.isl_schedule_node_type, visibility="public")
    num_children = cython.declare(int, visibility="public")
    parent_idx = cython.declare(int, visibility="public")
    index = cython.declare(int, visibility="public")
    label = cython.declare(str, visibility="public")
    location = cython.declare(list[int], visibility="public")
    loop_signature = cython.declare(list, visibility="public")
    expr = cython.declare(str, visibility="public")
    children_idx = cython.declare(list[str], visibility="public")

    def transform(self, tr: TrEnum, *args) -> cython.bint:
        """Execute the selected transformation.

        Args:
          TrEnum tr: Transformation `Enum`.
          args: Arguments passed to the transformation corresponding toe `trkey`.
        """

        nargs = len(args)
        target = TRANSFORMATIONS[tr].num_args()
        if nargs != target:
            raise ValueError(f"Number of args ({nargs}) for {tr} should be {target}")
        if not TRANSFORMATIONS[tr].valid(self):
            raise ValueError(f"Transformation {tr} not valied here:\n{self.yaml_str}")
        if not TRANSFORMATIONS[tr].valid_args(self, *args):
            tr_name = tr.__class__.__name__
            msg = f"Not valid {args=}, for {tr_name=}"
            raise ValueError(msg)
        # TODO proc_args (from olden times)
        self.scop._locate(self.location)
        # begin todo: this is ugly
        ps = self.scop.ptr_ccscop
        if ps.tmp_node != cython.NULL:
            isl.isl_schedule_node_free(ps.tmp_node)
        ps.tmp_node = isl.isl_schedule_node_copy(ps.current_node)
        ps.tmp_legal = ps.current_legal
        TRANSFORMATIONS[tr].transform(self.scop, *args)
        ps.current_legal = ps.check_legality()
        ps.modified = True
        # end todo: this is ugly
        return bool(self.scop.ptr_ccscop.current_legal)

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
        node.loop_signature = literal_eval(scop._get_loop_signature())
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

    def available_args(self, tr: TrEnum) -> list:
        """Describe available args."""
        return TRANSFORMATIONS[tr].available_args(self)

    def get_args(self, tr: TrEnum, start: int, end: int) -> list:
        expanded: list[list] = [[]]
        params = self.available_args(tr)
        if not params:
            return expanded
        if all([isinstance(p, list) for p in params]):
            return params
        for param in params:
            args = param
            if isinstance(param, LowerUpperBound):
                if param.lower is not None and param.lower > start:
                    start = param.lower
                if param.upper is not None and param.upper < end:
                    end = param.upper
                args = list(range(start, end))
                expanded = [[*e, a] for e in expanded for a in args]
            elif isinstance(param, list) and len(param) and isinstance(param[0], list):
                expanded = [[*e, *a] for e in expanded for a in args]
            else:
                expanded = [[*e, a] for e in expanded for a in args]
        return expanded

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


TRANSFORMATIONS = {}


def register(cls):
    """Register classes to TRANSFORMATIONS dict."""

    funcname = cls.__name__
    funcname = funcname.replace("Info", "")
    funcname = CAMEL_TO_SNAKE.sub("_", funcname).lower()
    cls.transform = getattr(w, funcname)
    TRANSFORMATIONS[TrEnum(funcname)] = cls
    return cls


class TransformInfo:
    """Abstract base class used to describe transformations."""

    func_name: str
    """The name of the C/C++ function in the `.so` file."""

    arg_help: list[str] = []
    """Help string describing the arg."""

    @staticmethod
    def valid(node: Node) -> bool:
        """Check that the transformation is valid on the node."""
        return node.node_type == NodeType.BAND

    @staticmethod
    def valid_args(node: Node, *arg, **kwargs) -> bool:
        """Check that args of the transformation is valid on node."""
        return True

    @staticmethod
    def _is_valid_stmt_idx(node: Node, idx: int) -> bool:
        return 0 <= idx < len(node.loop_signature)

    @staticmethod
    def _valid_idx_all_stmt(node: Node, idx: int, stmt_key: str) -> bool:
        return all(0 <= idx < len(s[stmt_key]) for s in node.loop_signature)

    @staticmethod
    def _is_valid_child_idx(node: Node, idx):
        return 0 <= idx and idx < len(node.children)

    @staticmethod
    def available_args(node: Node) -> list:
        """Return a list describing each of the args."""
        return []

    @classmethod
    def num_args(cls):
        return len(cls.arg_help)


def _tilable(node: Node, dim: int) -> bool:  # todo: try to move to Node
    for _ in range(dim):
        if node.node_type != NodeType.BAND:
            return False
        # if "tile" in node.label and "outer" in node.label:
        #     return False
        node = node.children[0]
    return True


@register
class Tile1DInfo(TransformInfo):
    arg_help = ["Tile size"]

    @staticmethod
    def valid(node: Node):
        return _tilable(node, 1)

    @staticmethod
    def valid_args(node, size1):
        return size1 > 1

    @staticmethod
    def available_args(node: Node):
        return [
            LowerUpperBound(lower=2, upper=None),
        ]


@register
class Tile2DInfo(TransformInfo):
    func_name = "tile2d"
    arg_help = ["Size1", "Size2"]

    @staticmethod
    def valid(node: Node):
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


@register
class Tile3DInfo(TransformInfo):
    func_name = "tile3d"
    arg_help = ["Size1", "Size2", "Size3"]

    @staticmethod
    def valid(node: Node):
        return _tilable(node, 3)

    @staticmethod
    def valid_args(node, size1, size2, size3):
        return size1 > 0 and size2 > 0 and size3 > 0

    @staticmethod
    def available_args(node: Node):
        return [
            LowerUpperBound(lower=2, upper=None),
            LowerUpperBound(lower=2, upper=None),
            LowerUpperBound(lower=2, upper=None),
        ]


@register
class InterchangeInfo(TransformInfo):
    func_name = "interchange"

    @staticmethod
    def valid(node: Node):
        return (
            node.node_type == NodeType.BAND
            and len(node.children) == 1
            and node.children[0].node_type == NodeType.BAND
        )


@register
class FuseInfo(TransformInfo):
    func_name = "fuse"
    arg_help = ["Index of first loop to fuse", "Index of second loop to fuse"]

    @staticmethod
    def valid(node: Node):
        return (
            (node.node_type == NodeType.SEQUENCE or node.node_type == NodeType.SET)
            and (len(node.children) > 1)
            and (all(ch.children[0].node_type == NodeType.BAND for ch in node.children))
        )

    @staticmethod
    def valid_args(node: Node, loop_idx1: int, loop_idx2: int):
        return (
            TransformInfo._is_valid_child_idx(node, loop_idx1)
            and TransformInfo._is_valid_child_idx(node, loop_idx2),
        )

    @staticmethod
    def available_args(node: Node):
        nc = len(node.children)
        args = []
        for arg1 in range(nc):
            for arg2 in range(arg1 + 1, nc):
                args.append([arg1, arg2])
        return args


@register
class FullFuseInfo(TransformInfo):
    func_name = "full_fuse"

    @staticmethod
    def valid(node: Node):
        return (
            node.node_type == NodeType.SEQUENCE or node.node_type == NodeType.SET
        ) and all(ch.children[0].node_type == NodeType.BAND for ch in node.children)


@register
class SplitInfo(TransformInfo):
    func_name = "split"
    arg_help = ["Index where the sequence should be split"]

    @staticmethod
    def valid(node: Node):
        if node.node_type not in [NodeType.SEQUENCE, NodeType.SET]:
            return False
        if len(node.children) < 2:
            return False
        if node.parent.node_type != NodeType.BAND:
            return False
        args = SplitInfo.available_args(node)
        if any([isinstance(a, LowerUpperBound) and a.lower >= a.upper for a in args]):
            return False
        return args is not None

    @staticmethod
    def valid_args(node: Node, split_idx: int) -> bool:
        nc = len(node.children)
        return 1 <= split_idx and split_idx < nc - 1

    @staticmethod
    def available_args(node: Node) -> list:
        nc = len(node.children)
        return [LowerUpperBound(lower=1, upper=nc - 1)]


@register
class FullSplitInfo(TransformInfo):
    func_name = "full_split"

    # TODO -> split sequence!
    @staticmethod
    def valid(node: Node):
        if node.node_type not in [NodeType.SEQUENCE, NodeType.SET]:
            return False
        if node.parent.node_type != NodeType.BAND:
            return False
        return True


@register
class PartialShiftVarInfo(TransformInfo):
    func_name = "partial_shift_var"
    arg_help = ["Statement index", "Variable index", "Coefficient"]

    @staticmethod
    def valid_args(node: Node, stmt_idx: int, var_idx: int, coeff: int):
        args = PartialShiftVarInfo.available_args(node)
        if not args:
            return []
        return [stmt_idx, var_idx] in args[0]

    @staticmethod
    def available_args(node: Node):
        args = []
        for stmt_idx, ls in enumerate(node.loop_signature):
            for var_idx in range(len(ls["vars"])):
                args.append([stmt_idx, var_idx])
        return [args, LowerUpperBound()]


@register
class PartialShiftValInfo(TransformInfo):
    func_name = "partial_shift_val"
    arg_help = ["Statement index", "Value"]

    @staticmethod
    def valid_args(node: Node, stmt_idx: int, value: int):
        return TransformInfo._is_valid_stmt_idx(node, stmt_idx)

    @staticmethod
    def available_args(node: Node):
        ns = len(node.loop_signature)
        return [LowerUpperBound(lower=0, upper=ns), LowerUpperBound()]


@register
class PartialShiftParamInfo(TransformInfo):
    func_name = "partial_shift_param"
    arg_help = ["Statement index", "Parameter index", "Coefficient"]

    @staticmethod
    def valid(node: Node) -> bool:
        if node.node_type != NodeType.BAND:
            return False
        args = PartialShiftParamInfo.available_args(node)
        if not args:
            return False
        return bool(args[0])

    @staticmethod
    def valid_args(node: Node, stmt_idx: int, param_idx: int, coeff: int):
        args = PartialShiftParamInfo.available_args(node)
        if not args:
            return False
        return [stmt_idx, param_idx] in args[0]

    @staticmethod
    def available_args(node: Node):
        args = []
        for stmt_idx, ls in enumerate(node.loop_signature):
            for param_idx in range(len(ls["params"])):
                args.append([stmt_idx, param_idx])
        return [args, LowerUpperBound()]


@register
class FullShiftVarInfo(TransformInfo):
    func_name = "full_shift_var"
    arg_help = ["Variable index", "Coefficient"]

    @staticmethod
    def valid(node: Node) -> bool:
        if node.node_type != NodeType.BAND:
            return False
        args = FullShiftVarInfo.available_args(node)
        if not args:
            return False
        return bool(args[0])

    @staticmethod
    def valid_args(node: Node, var_idx: int, _coeff: int):
        args = FullShiftVarInfo.available_args(node)
        if not args:
            return []
        return var_idx in args[0]

    @staticmethod
    def available_args(node: Node):
        if not all(s["vars"] for s in node.loop_signature):
            return []
        # "transpose" loop signatures
        zs = zip(*[s["vars"] for s in node.loop_signature])
        # var is same at idx for all loop_signatures
        same = [len(set(z)) == 1 for z in zs]
        # index of the first "false" in same (or len(same))
        diff_idx = same.index(False) if not all(same) else len(same)
        return [list(range(diff_idx)), LowerUpperBound()]


@register
class FullShiftValInfo(TransformInfo):
    func_name = "full_shift_val"
    arg_help = ["Value"]

    @staticmethod
    def available_args(node: Node):
        return [LowerUpperBound()]


@register
class FullShiftParamInfo(TransformInfo):
    func_name = "full_shift_param"
    arg_help = ["Parameter index", "Coefficient"]

    @staticmethod
    def valid(node: Node) -> bool:
        if node.node_type != NodeType.BAND:
            return False
        args = FullShiftParamInfo.available_args(node)
        if not args:
            return False
        return bool(args[0])

    @staticmethod
    def valid_args(node: Node, param_idx: int, coeff: int):
        args = FullShiftParamInfo.available_args(node)
        if not args:
            return False
        return param_idx in args[0]

    @staticmethod
    def available_args(node: Node):
        if not all(s["params"] for s in node.loop_signature):
            return []
        min_np = len(node.loop_signature[0]["params"])
        return [list(range(min_np)), LowerUpperBound()]


@register
class SetParallelInfo(TransformInfo):
    func_name = "set_parallel"
    arg_help = ["omp num_threads"]

    @staticmethod
    def available_args(node: Node):
        nproc = multiprocessing.cpu_count()
        return [
            LowerUpperBound(0, nproc),
        ]


@register
class SetLoopOptInfo(TransformInfo):
    func_name = "set_loop_opt"
    arg_help = ["Iterator index", "Option"]

    @staticmethod
    def available_args(node: Node):
        # TODO: I don't know the first element
        return [
            LowerUpperBound(0, 1),
            [
                AstLoopType.DEFAULT.value,
                AstLoopType.ATOMIC.value,
                AstLoopType.SEPARATE.value,
            ],
        ]


@cython.cclass
class Scop:
    ptr_ccscop: cython.pointer(ccScop)

    @staticmethod
    @cython.cfunc
    def create(ptr: cython.pointer(ccScop)) -> Scop:
        scop = Scop()
        scop.ptr_ccscop = ptr
        return scop

    @property
    def schedule_tree(self) -> list[Node]:
        self._goto_root()
        nodes: list[Node] = []
        self._traverse(nodes, parent=-1, location=[])
        return nodes

    @property
    def legal(self) -> bool:
        return bool(self.ptr_ccscop.current_legal)

    def transform_list(self, trs: list) -> list[bool]:
        result = []
        for node_idx, tr, *args in trs:
            node = self.schedule_tree[node_idx]
            result.append(node.transform(tr, *args))
        return result

    def reset(self):
        self.ptr_ccscop.reset()

    def rollback(self) -> None:
        """Roll back (revert) the last transformation."""
        self.ptr_ccscop.rollback()

    def __repr__(self):  # todo this is not a good node representation
        node = self.ptr_ccscop.current_node
        return isl.isl_schedule_node_to_str(node).decode()

    @cython.cfunc
    def _cur(self) -> isl.schedule_node:
        # shortcut to save typing
        return self.ptr_ccscop.current_node

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

    def _get_loop_signature(self) -> str:
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
        cur = self.ptr_ccscop.current_node
        mupa = isl.isl_schedule_node_band_get_partial_schedule(cur)
        expr = isl.isl_multi_union_pw_aff_to_str(mupa)
        mupa = isl.isl_multi_union_pw_aff_free(mupa)
        return expr.decode()

    def _goto_root(self) -> None:
        ptr = self.ptr_ccscop.current_node
        ptr = isl.isl_schedule_node_root(ptr)
        self.ptr_ccscop.current_node = ptr

    def _goto_parent(self) -> None:
        ptr = self.ptr_ccscop.current_node
        ptr = isl.isl_schedule_node_parent(ptr)
        self.ptr_ccscop.current_node = ptr

    def _goto_child(self, n: int) -> None:
        ptr = self.ptr_ccscop.current_node
        ptr = isl.isl_schedule_node_child(ptr, n)
        self.ptr_ccscop.current_node = ptr

    def _locate(self, loc: list[int]) -> None:
        if self.ptr_ccscop.current_node == cython.NULL:
            raise RuntimeError(DELETED_TRANSLATOR_EXCMSG)
        self._goto_root()
        for child in loc:
            self._goto_child(child)

    def _yaml_str(self) -> str:
        node = self.ptr_ccscop.current_node
        return isl.isl_schedule_node_to_str(node).decode()

    def _traverse(self, nodes: list[Node], parent: int, location: list[int]):
        current_idx = len(nodes)
        node = Node.create(self.ptr_ccscop, parent, current_idx, location)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                self._goto_child(c)
                node.children_idx[c] = len(nodes)
                self._traverse(nodes, current_idx, location + [c])
                self._goto_parent()
