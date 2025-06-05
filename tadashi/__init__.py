#!/usr/bin/env python

"""Main Tadashi package."""

from __future__ import annotations

import multiprocessing
import os
from ast import literal_eval
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Optional

if os.environ.get("READTHEDOCS") != "True":
    from ctadashi import ctadashi


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


class NodeType(Enum):
    """Type of the schedule tree node.

    Details: `ISL online user manual (Schedule Trees)`_.

    .. _ISL online user manual (Schedule Trees):
       https://libisl.sourceforge.io/user.html#Schedule-Trees
    """

    BAND = 0
    CONTEXT = auto()
    DOMAIN = auto()
    EXPANSION = auto()
    EXTENSION = auto()
    FILTER = auto()
    LEAF = auto()
    GUARD = auto()
    MARK = auto()
    SEQUENCE = auto()
    SET = auto()


class TrEnum(StrEnum):
    """Enums of implemented transformations.

    One of these enums needs to be passed to `Node.transform()` (with
    args) to perform the transformation.
    """

    TILE1D = auto()
    TILE2D = auto()
    TILE3D = auto()
    INTERCHANGE = auto()
    FUSE = auto()
    FULL_FUSE = auto()
    SPLIT = auto()
    FULL_SPLIT = auto()
    PARTIAL_SHIFT_VAR = auto()
    PARTIAL_SHIFT_VAL = auto()
    FULL_SHIFT_VAR = auto()
    FULL_SHIFT_VAL = auto()
    FULL_SHIFT_PARAM = auto()
    PARTIAL_SHIFT_PARAM = auto()
    SET_PARALLEL = auto()
    SET_LOOP_OPT = auto()

    def __repr__(self):
        return f"TrEnum.{self.value.upper()}"


@dataclass
class Node:
    """Schedule node (Python representation)."""

    #: Pointer to the `Scop` object the node belongs to.
    scop: "Scop"

    #: Type of the node in the schedule tree.
    node_type: NodeType

    #: Number of children of the node in the schedule tree.
    num_children: int

    #: The index of the parent of the node in the schedule tree
    #: according to `Scop.schedule_tree`.
    parent_idx: int

    #: The index of the current node in `Scop.schedule_tree`.
    index: int

    #: A string identifying the node.
    label: str

    #: List of child indexes which determine the location of the node
    #: starting from the root.  See `Scop.locate`.
    location: list[int]

    #: Description of the band nodes (see `Scop.get_loop_signature`).
    loop_signature: list[dict]

    #: The ISL expression of the schedule node.
    expr: str

    #: Index of the children in `Scop.schedule_tree`.
    children_idx: list[str]

    @property
    def parent(self):
        """The node which is the parent of the current node."""
        return self.scop.schedule_tree[self.parent_idx]

    @property
    def children(self):
        """List of nodes which are the children of the current node."""
        return [self.scop.schedule_tree[i] for i in self.children_idx]

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

    def locate(self):
        """Set the `current_node` to point to `self`."""
        self.scop.locate(self.location)
        return self.scop.get_current_node_from_ISL(None, None)

    def transform(self, trkey: TrEnum, *args) -> bool:
        """Execute the selected transformation.

        Args:
          TrEnum trkey: Transformation `Enum`.
          args: Arguments passed to the transformation corresponding toe `trkey`.
        """
        # TODO proc_args
        tr = TRANSFORMATIONS[trkey]
        if len(args) != len(tr.arg_help):
            raise ValueError(
                f"Incorrect number of args ({len(args)} should be {len(tr.arg_help)}) for {tr}!"
            )
        if not tr.valid(self):
            msg = f"Not a valid transformation: {tr}"
            raise ValueError(msg)
        if not tr.valid_args(self, *args):
            msg = f"Not valid transformation args: {args}"
            raise ValueError(msg)

        func = getattr(ctadashi, tr.func_name)
        self.scop.locate(self.location)
        legal = func(self.scop.pool_idx, self.scop.scop_idx, *args)
        return bool(legal)

    @property
    def yaml_str(self):
        self.scop.locate(self.location)
        encoded_result = ctadashi.print_schedule_node(
            self.scop.pool_idx, self.scop.scop_idx
        )
        return encoded_result

    def rollback(self) -> None:
        """Roll back (revert) the last transformation."""
        ctadashi.rollback(self.scop.pool_idx, self.scop.scop_idx)

    @property
    def valid_transformation(self, tr: TrEnum) -> bool:
        """Check the validity of the transformation."""
        return TRANSFORMATIONS[tr].valid(self)

    @property
    def available_transformations(self) -> list[TrEnum]:
        """List transformations available at the `Node`."""
        result = []
        for k, tr in TRANSFORMATIONS.items():
            if tr.valid(self):
                result.append(k)
        return result

    def valid_args(self, tr: TrEnum, *args) -> bool:
        """Check the validity of args."""
        return TRANSFORMATIONS[tr].valid_args(self, *args)

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


LowerUpperBound = namedtuple(
    "LowerUpperBound", ["lower", "upper"], defaults=[None, None]
)
"""Integer interval description.

Lower and upper bounds for describing (integer) intervals of valid
arguments for transformations. `None` indicates no upper/lower bound.

"""


class TransformInfo:
    """Abstract base class used to describe transformations."""

    #: The name of the C/C++ function in the `.so` file.
    func_name: str
    #: Help string describing the arg.
    arg_help: list[str] = []

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


def _tilable(node: Node, dim: int) -> bool:
    for _ in range(dim):
        if node.node_type != NodeType.BAND:
            return False
        if "tiled" in node.label and "outer" in node.label:
            return False
        node = node.children[0]
    return True


class Tile1DInfo(TransformInfo):
    func_name = "tile1d"
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
            LowerUpperBound(lower=1, upper=None),
        ]


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
            LowerUpperBound(lower=1, upper=None),
            LowerUpperBound(lower=1, upper=None),
        ]


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
            LowerUpperBound(lower=1, upper=None),
            LowerUpperBound(lower=1, upper=None),
            LowerUpperBound(lower=1, upper=None),
        ]


class InterchangeInfo(TransformInfo):
    func_name = "interchange"

    @staticmethod
    def valid(node: Node):
        return (
            node.node_type == NodeType.BAND
            and len(node.children) == 1
            and node.children[0].node_type == NodeType.BAND
        )


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


class FullFuseInfo(TransformInfo):
    func_name = "full_fuse"

    @staticmethod
    def valid(node: Node):
        return (
            node.node_type == NodeType.SEQUENCE or node.node_type == NodeType.SET
        ) and all(ch.children[0].node_type == NodeType.BAND for ch in node.children)


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


class FullShiftValInfo(TransformInfo):
    func_name = "full_shift_val"
    arg_help = ["Value"]

    @staticmethod
    def available_args(node: Node):
        return [LowerUpperBound()]


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


class SetParallelInfo(TransformInfo):
    func_name = "set_parallel"
    arg_help = ["omp num_threads"]

    @staticmethod
    def available_args(node: Node):
        nproc = multiprocessing.cpu_count()
        return [
            LowerUpperBound(0, nproc),
        ]


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


"""A dictionary which connects the simple `TrEnum` to the detailed
`TranformInfo`."""
TRANSFORMATIONS: dict[TrEnum, TransformInfo] = {
    TrEnum.TILE1D: Tile1DInfo(),
    TrEnum.TILE2D: Tile2DInfo(),
    TrEnum.TILE3D: Tile3DInfo(),
    TrEnum.INTERCHANGE: InterchangeInfo(),
    TrEnum.FUSE: FuseInfo(),
    TrEnum.FULL_FUSE: FullFuseInfo(),
    TrEnum.SPLIT: SplitInfo(),
    TrEnum.FULL_SPLIT: FullSplitInfo(),
    TrEnum.FULL_SHIFT_VAL: FullShiftValInfo(),
    TrEnum.PARTIAL_SHIFT_VAL: PartialShiftValInfo(),
    TrEnum.FULL_SHIFT_VAR: FullShiftVarInfo(),
    TrEnum.PARTIAL_SHIFT_VAR: PartialShiftVarInfo(),
    TrEnum.FULL_SHIFT_PARAM: FullShiftParamInfo(),
    TrEnum.PARTIAL_SHIFT_PARAM: PartialShiftParamInfo(),
    TrEnum.SET_PARALLEL: SetParallelInfo(),
    TrEnum.SET_LOOP_OPT: SetLoopOptInfo(),
}


class Scop:
    """One SCoP in `Scops`, a loop nest (to use a rough analogy).

    In the .so file, there is a global `std::vector` of `isl_scop`
    objects.  Objects of `Scop` (in python) represents a the
    `isl_scop` object by storing its index in the `std::vector`.

    """

    def __init__(self, pool_idx, scop_idx) -> None:
        self.pool_idx = pool_idx
        self.scop_idx = scop_idx

    def get_loop_signature(self):
        """Extract the value for `Node.loop_signature`.

        A "loop signature", contains the information which is relevant
        for the shift transformations.  Loop signature is a list.
        The entries in this list describes the parameters and iteration
        variables of each statement covered by the loop/band node.

        """
        loop_signature = ctadashi.get_loop_signature(self.pool_idx, self.scop_idx)
        return literal_eval(loop_signature)

    def _make_node(self, parent, current_idx, location):
        num_children = ctadashi.get_num_children(self.pool_idx, self.scop_idx)
        node = Node(
            scop=self,
            node_type=NodeType(ctadashi.get_type(self.pool_idx, self.scop_idx)),
            num_children=num_children,
            parent_idx=parent,
            index=current_idx,
            label=ctadashi.get_label(self.pool_idx, self.scop_idx),
            location=location,
            loop_signature=self.get_loop_signature(),
            expr=ctadashi.get_expr(self.pool_idx, self.scop_idx),
            children_idx=[-1] * num_children,
        )
        return node

    def _traverse(self, nodes, parent, location):
        current_idx = len(nodes)
        node = self._make_node(parent, current_idx, location)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                ctadashi.goto_child(self.pool_idx, self.scop_idx, c)
                node.children_idx[c] = len(nodes)
                self._traverse(nodes=nodes, parent=current_idx, location=location + [c])
                ctadashi.goto_parent(self.pool_idx, self.scop_idx)

    @property
    def schedule_tree(self) -> list[Node]:
        ctadashi.goto_root(self.pool_idx, self.scop_idx)
        nodes: list[Node] = []
        self._traverse(nodes, parent=-1, location=[])
        return nodes

    def locate(self, location: list[int]):
        """Update the current node on the C/C++ side."""
        ctadashi.goto_root(self.pool_idx, self.scop_idx)
        for c in location:
            ctadashi.goto_child(self.pool_idx, self.scop_idx, c)

    def transform_list(self, trs: list) -> list[bool]:
        result = []
        for node_idx, tr, *args in trs:
            node = self.schedule_tree[node_idx]
            result.append(node.transform(tr, *args))
        return result

    def reset(self):
        ctadashi.reset_scop(self.pool_idx, self.scop_idx)


class Scops:
    """All SCoPs which belong to a given file.

    The object of type `Scops` is similar to a list."""

    pool_idx: int
    num_scops: int
    scops: list[Scop]

    def __init__(self, source_path: str):
        self._check_missing_file(Path(source_path))
        self.pool_idx = ctadashi.init_scops(str(source_path))
        self.num_scops = ctadashi.num_scops(self.pool_idx)
        self.scops = [Scop(self.pool_idx, scop_idx=i) for i in range(self.num_scops)]

    def __del__(self):
        ctadashi.free_scops(self.pool_idx)

    @staticmethod
    def _check_missing_file(path: Path):
        if not path.exists():
            raise ValueError(f"{path} does not exist!")

    def generate_code(self, input_path, output_path):
        """Generate the source code.

        The transformations happen on the SCoPs (polyhedral
        representations), and to put that into code, this method needs
        to be called.

        """
        ctadashi.generate_code(self.pool_idx, str(input_path), str(output_path))

    def __len__(self):
        return self.num_scops

    def __getitem__(self, idx):
        return self.scops[idx]
