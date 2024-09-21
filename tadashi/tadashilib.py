#!/usr/bin/env python

"""Main Tadashi package."""

# from ctypes import CDLL, c_bool, c_char_p, c_int, c_long, c_size_t
from __future__ import annotations

import ctypes
import os
from ast import literal_eval
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Optional

from .apps import App


class AstLoopType(Enum):
    """Possible values for `SET_LOOP_OPT`.

    `UNROLL` should be avoided unless the remarks in the :ref:`Docs`.

    ### Docs
    `ISL online user manual (AST generation options)`_.

    .. _ISL online user manual (AST generation options):
       https://libisl.sourceforge.io/user.html#AST-Generation-Options-Schedule-Tree
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

    TILE = auto()
    INTERCHANGE = auto()
    FUSE = auto()
    FULL_FUSE = auto()
    PARTIAL_SHIFT_VAR = auto()
    PARTIAL_SHIFT_VAL = auto()
    FULL_SHIFT_VAR = auto()
    FULL_SHIFT_VAL = auto()
    FULL_SHIFT_PARAM = auto()
    PARTIAL_SHIFT_PARAM = auto()
    SET_PARALLEL = auto()
    SET_LOOP_OPT = auto()
    PRINT_SCHEDULE_NODE = auto()


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

    #: List of child indexes which determine the location of the node
    #: starting from the root.  See `Scop.locate`.
    location: list[int]

    #: .. todo:: Description of the band nodes.
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
        words = [
            "Node type:",
            f"{self.node_type},",
            f"{self.loop_signature},",
            f"{self.expr},",
            f"{self.location}",
        ]
        return " ".join(words)

    def locate(self):
        """Set the `current_node` in `ctadashi` to point to the
        current `Node`."""
        self.scop.locate(self.location)
        return self.scop.get_current_node_from_ISL(None, None)

    @property
    def available_transformations(self) -> list[TrEnum]:
        """List of transformations available at the `Node`."""
        result = []
        for k, tr in TRANSFORMATIONS.items():
            if tr.valid(self):
                result.append(k)
        return result

    def transform(self, trkey: TrEnum, *args):
        """Execute the selected transformation.

        Args:
          TrEnum trkey: Transformation `Enum`.
          args: Arguments passed to the transformation corresponding toe `trkey`.
        """
        # TODO proc_args
        tr = TRANSFORMATIONS[trkey]
        if len(args) != len(tr.arg_help):
            raise ValueError(f"Incorrect number of args for {tr}!")
        if not tr.valid(self):
            msg = f"Not a valid transformation: {tr}"
            raise ValueError(msg)
        if not tr.valid_args(self, *args):
            msg = f"Not valid transformation args: {args}"
            raise ValueError(msg)

        func = getattr(self.scop.ctadashi, tr.func_name)
        self.scop.locate(self.location)
        return func(self.scop.idx, *args)

    def rollback(self):
        """Roll back (revert) the last transformation."""
        self.scop.ctadashi.rollback(self.scop.idx)

    def valid_args(self, tr: TrEnum, *args):
        return TRANSFORMATIONS[tr].valid_args(self, *args)

    def available_args(self, tr: TrEnums):
        return TRANSFORMATIONS[tr].available_args(self)


LowerUpperBound = namedtuple(
    "LowerUpperBound", ["lower", "upper"], defaults=[None, None]
)


class TransformInfo:
    func_name: str
    argtypes: list[type] = []
    arg_help: list[str] = []
    restype: Optional[type] = ctypes.c_bool

    @staticmethod
    def valid(node: Node) -> bool:
        return node.node_type == NodeType.BAND

    @staticmethod
    def valid_args(node: Node, *arg, **kwargs) -> bool:
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
        return []


class TileInfo(TransformInfo):
    func_name = "tile"
    argtypes = [ctypes.c_size_t]
    arg_help = ["Tile size"]
    restype = ctypes.c_bool

    @staticmethod
    def valid_args(node, arg):
        return True

    @staticmethod
    def available_args(node: Node):
        return [LowerUpperBound(lower=1, upper=None)]


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
    argtypes = [ctypes.c_int, ctypes.c_int]
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
        return [
            LowerUpperBound(lower=0, upper=nc),
            LowerUpperBound(lower=0, upper=nc),
        ]


class FullFuseInfo(TransformInfo):
    func_name = "full_fuse"

    @staticmethod
    def valid(node: Node):
        return (
            node.node_type == NodeType.SEQUENCE or node.node_type == NodeType.SET
        ) and all(ch.children[0].node_type == NodeType.BAND for ch in node.children)


class FullShiftValInfo(TransformInfo):
    func_name = "full_shift_val"
    argtypes = [ctypes.c_long]
    arg_help = ["Value"]

    @staticmethod
    def available_args(node: Node):
        return [LowerUpperBound()]


class PartialShiftValInfo(TransformInfo):
    func_name = "partial_shift_val"
    argtypes = [ctypes.c_int, ctypes.c_long]
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
    argtypes = [ctypes.c_long, ctypes.c_long]
    arg_help = ["Coefficient", "Variable index"]

    @staticmethod
    def valid_args(node: Node, _coeff: int, var_idx: int):
        return TransformInfo._valid_idx_all_stmt(node, var_idx, "vars")

    @staticmethod
    def available_args(node: Node):
        min_nv = min(len(s["vars"]) for s in node.loop_signature)
        return [LowerUpperBound(), LowerUpperBound(lower=0, upper=min_nv)]


class PartialShiftVarInfo(TransformInfo):
    func_name = "partial_shift_var"
    argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_long]
    arg_help = ["Statement index", "Coefficient", "Variable index"]

    @staticmethod
    def valid_args(node: Node, stmt_idx: int, coeff: int, var_idx: int):
        return (
            TransformInfo._is_valid_stmt_idx(node, stmt_idx)
            and 0 <= var_idx < len(node.loop_signature[stmt_idx]["vars"]),
        )

    @staticmethod
    def available_args(node: Node):
        min_nv = min(len(s["vars"]) for s in node.loop_signature)
        return [
            LowerUpperBound(0, len(node.loop_signature)),
            LowerUpperBound(),
            LowerUpperBound(0, min_nv),
        ]


class FullShiftParamInfo(TransformInfo):
    func_name = "full_shift_param"
    argtypes = [ctypes.c_long, ctypes.c_long]
    arg_help = ["Coefficient", "Parameter index"]

    @staticmethod
    def valid_args(node: Node, coeff: int, param_idx: int):
        return TransformInfo._valid_idx_all_stmt(node, param_idx, "params")

    @staticmethod
    def available_args(node: Node):
        min_np = min(len(s["params"]) for s in node.loop_signature)
        return [LowerUpperBound(), LowerUpperBound(0, min_np)]


class PartialShiftParamInfo(TransformInfo):
    func_name = "partial_shift_param"
    argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_long]
    arg_help = ["Statement index", "Coefficient", "Parameter index"]

    @staticmethod
    def valid_args(node: Node, stmt_idx: int, coeff: int, param_idx: int):
        return (
            TransformInfo._is_valid_stmt_idx(node, param_idx)
            and 0 <= param_idx
            and param_idx < len(node.loop_signature[stmt_idx]["params"]),
        )

    @staticmethod
    def available_args(node: Node):
        min_np = min(len(s["params"]) for s in node.loop_signature)
        return [
            LowerUpperBound(0, len(node.loop_signature)),
            LowerUpperBound(),
            LowerUpperBound(0, min_np),
        ]


class SetParallelInfo(TransformInfo):
    func_name = "set_parallel"


class SetLoopOptInfo(TransformInfo):
    func_name = "set_loop_opt"
    argtypes = [ctypes.c_int, ctypes.c_int]
    arg_help = ["Iterator index", "Option"]

    @staticmethod
    def available_args(node: Node):
        # TODO: I don't know the first element
        return [
            LowerUpperBound(0, 1),
            [
                AstLoopType.DEFAULT,
                AstLoopType.ATOMIC,
                AstLoopType.SEPARATE,
            ],
        ]


class PrintScheduleNodeInfo(TransformInfo):
    func_name = "print_schedule_node"

    @staticmethod
    def valid(node: Node) -> bool:
        return True


TRANSFORMATIONS: dict[TrEnum, TransformInfo] = {
    TrEnum.TILE: TileInfo(),
    TrEnum.INTERCHANGE: InterchangeInfo(),
    TrEnum.FUSE: FuseInfo(),
    TrEnum.FULL_FUSE: FullFuseInfo(),
    TrEnum.FULL_SHIFT_VAL: FullShiftValInfo(),
    TrEnum.PARTIAL_SHIFT_VAL: PartialShiftValInfo(),
    TrEnum.FULL_SHIFT_VAR: FullShiftVarInfo(),
    TrEnum.PARTIAL_SHIFT_VAR: PartialShiftVarInfo(),
    TrEnum.FULL_SHIFT_PARAM: FullShiftParamInfo(),
    TrEnum.PARTIAL_SHIFT_PARAM: PartialShiftParamInfo(),
    TrEnum.SET_PARALLEL: SetParallelInfo(),
    TrEnum.SET_LOOP_OPT: SetLoopOptInfo(),
    # TrEnum.PRINT_SCHEDULE_NODE: PrintScheduleNodeInfo(),
}


class Scop:
    """Single SCoP.

    In the .so file, there is a global `std::vector` of `isl_scop`
    objects.  Objects of `Scop` (in python) represents a the
    `isl_scop` object by storing its index in the `std::vecto`.
    """

    def __init__(self, idx, ctadashi) -> None:
        self.ctadashi = ctadashi
        self.idx = idx

    def get_loop_signature(self):
        loop_signature = self.ctadashi.get_loop_signature(self.idx).decode()
        return literal_eval(loop_signature)

    def make_node(self, parent, location):
        num_children = self.ctadashi.get_num_children(self.idx)
        node = Node(
            scop=self,
            node_type=NodeType(self.ctadashi.get_type(self.idx)),
            num_children=num_children,
            parent_idx=parent,
            location=location,
            loop_signature=self.get_loop_signature(),
            expr=self.ctadashi.get_expr(self.idx).decode("utf-8"),
            children_idx=[-1] * num_children,
        )
        return node

    def traverse(self, nodes, parent, location):
        node = self.make_node(parent, location)
        current_idx = len(nodes)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                self.ctadashi.goto_child(self.idx, c)
                node.children_idx[c] = len(nodes)
                self.traverse(nodes=nodes, parent=current_idx, location=location + [c])
                self.ctadashi.goto_parent(self.idx)

    @property
    def schedule_tree(self) -> list[Node]:
        self.ctadashi.goto_root(self.idx)
        nodes: list[Node] = []
        self.traverse(nodes, parent=-1, location=[])
        return nodes

    def locate(self, location: list[int]):
        self.ctadashi.goto_root(self.idx)
        for c in location:
            self.ctadashi.goto_child(self.idx, c)


class Scops:
    """All SCoPs which belong to a given file.

    The object of type `Scops` is similar to a list."""

    def __init__(self, app: App):
        self.setup_ctadashi(app)
        self.check_missing_file(app.source_path)
        self.num_changes = 0
        self.app = app
        self.source_path_bytes = str(self.app.source_path).encode()
        self.num_scops = self.ctadashi.init_scops(self.source_path_bytes)
        self.scops = [Scop(i, self.ctadashi) for i in range(self.num_scops)]

    def setup_ctadashi(self, app: App):
        os.environ["C_INCLUDE_PATH"] = ":".join(map(str, app.include_paths))
        self.so_path = Path(__file__).parent.parent / "build/libctadashi.so"
        self.check_missing_file(self.so_path)
        self.ctadashi = ctypes.CDLL(str(self.so_path))
        self.ctadashi.init_scops.argtypes = [ctypes.c_char_p]
        self.ctadashi.init_scops.restype = ctypes.c_int
        self.ctadashi.get_type.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_type.restype = ctypes.c_int
        self.ctadashi.get_num_children.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_num_children.restype = ctypes.c_size_t
        self.ctadashi.goto_parent.argtypes = [ctypes.c_size_t]
        self.ctadashi.goto_child.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        self.ctadashi.get_expr.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_expr.restype = ctypes.c_char_p
        self.ctadashi.get_loop_signature.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_loop_signature.restype = ctypes.c_char_p
        self.ctadashi.print_schedule_node.argtypes = [ctypes.c_size_t]
        self.ctadashi.print_schedule_node.restype = None
        self.ctadashi.goto_root.argtypes = [ctypes.c_size_t]
        self.ctadashi.generate_code.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        #
        for tr_name, tr_info in TRANSFORMATIONS.items():
            msg = f"The transformation {tr_name} is not specified correctly!"
            assert len(tr_info.arg_help) == len(tr_info.argtypes), msg
            func = getattr(self.ctadashi, tr_info.func_name)
            func.argtypes = [ctypes.c_size_t] + tr_info.argtypes
            func.restype = tr_info.restype

    @staticmethod
    def check_missing_file(path: Path):
        if not path.exists():
            raise ValueError(f"{path} does not exist!")

    def get_input_path_bytes_and_backup_source(self):
        """Get the 'input' to `generate_code()` which is a copy of the
        current 'source'."""
        file_name = self.app.source_path.with_suffix("")
        file_ext = self.app.source_path.suffix

        # find a path which doesn't exist
        input_path = Path(f"{file_name}-{self.num_changes}{file_ext}")
        self.num_changes += 1
        while input_path.exists():
            input_path = Path(f"{file_name}-{self.num_changes}{file_ext}")
            self.num_changes += 1

        # copy source_path to input_path
        input_path.write_text(self.app.source_path.read_text())
        input_path_bytes = str(input_path).encode()
        return input_path_bytes

    def generate_code(self, input_path="", output_path=""):
        output_path_bytes = str(output_path).encode()
        if not output_path:
            output_path_bytes = self.source_path_bytes
        input_path_bytes = str(input_path).encode()
        if not input_path:
            # rewrite the original source_path file with the generated code
            input_path_bytes = self.get_input_path_bytes_and_backup_source()
        self.ctadashi.generate_code(input_path_bytes, output_path_bytes)

    def __len__(self):
        return self.num_scops

    def __getitem__(self, idx):
        return self.scops[idx]

    def __del__(self):
        self.ctadashi.free_scops()
