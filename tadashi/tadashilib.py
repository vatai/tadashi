#!/usr/bin/env python

# from ctypes import CDLL, c_bool, c_char_p, c_int, c_long, c_size_t
from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Callable

from .apps import App


class NodeType(Enum):
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


@dataclass
class TransformationInfo:
    func_name: str
    argtypes: list[type]
    arg_help: list[str]
    restype: type
    valid: Callable[[Node], bool]
    args_valid: list[Callable]


class Transformation(StrEnum):
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
    PRINT_SCHEDULE = auto()
    SET_LOOP_OPT = auto()


TRANSFORMATIONS = {
    Transformation.TILE: TransformationInfo(
        func_name="tile",
        argtypes=[ctypes.c_size_t],
        arg_help=["Tile size"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[lambda node, arg: isinstance(arg, int) and arg > 0],
    ),
    Transformation.INTERCHANGE: TransformationInfo(
        func_name="interchange",
        argtypes=[],
        arg_help=[],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND
        and len(node.children) == 1
        and node.children[0].node_type == NodeType.BAND,
        args_valid=[],
    ),
    Transformation.FUSE: TransformationInfo(
        func_name="fuse",
        argtypes=[ctypes.c_int, ctypes.c_int],
        arg_help=["Index of first loop to fuse", "Index of second loop to fuse"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.SEQUENCE,
        # to generte valid params, we need read it from the node
        args_valid=[],
    ),
    Transformation.FULL_FUSE: TransformationInfo(
        func_name="full_fuse",
        argtypes=[],
        arg_help=[],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.SEQUENCE,
        args_valid=[],
    ),
    Transformation.FULL_SHIFT_VAL: TransformationInfo(
        func_name="full_shift_val",
        argtypes=[ctypes.c_long],
        arg_help=["Value"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[],
    ),
    Transformation.PARTIAL_SHIFT_VAL: TransformationInfo(
        func_name="partial_shift_val",
        argtypes=[ctypes.c_int, ctypes.c_long],
        arg_help=["Statement index", "Value"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[],
    ),
    Transformation.FULL_SHIFT_VAR: TransformationInfo(
        func_name="full_shift_var",
        argtypes=[ctypes.c_long, ctypes.c_long],
        arg_help=["Coefficient", "Variable index"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[],
    ),
    Transformation.PARTIAL_SHIFT_VAR: TransformationInfo(
        func_name="partial_shift_var",
        argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_long],
        arg_help=["Statement index", "Coefficient", "Variable index"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[],
    ),
    Transformation.FULL_SHIFT_PARAM: TransformationInfo(
        func_name="full_shift_param",
        argtypes=[ctypes.c_long, ctypes.c_long],
        arg_help=["Coefficient", "Parameter index"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[],
    ),
    Transformation.PARTIAL_SHIFT_PARAM: TransformationInfo(
        func_name="partial_shift_param",
        argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_long],
        arg_help=["Statement index", "Coefficient", "Parameter index"],
        restype=ctypes.c_bool,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[],
    ),
    Transformation.SET_LOOP_OPT: TransformationInfo(
        func_name="set_loop_opt",
        argtypes=[ctypes.c_int, ctypes.c_int],
        arg_help=["Iterator index", "Option"],
        restype=None,
        valid=lambda node: node.node_type == NodeType.BAND,
        args_valid=[],
    ),
}


@dataclass
class Node:
    scop: "Scop"
    node_type: NodeType
    num_children: int
    parent_idx: int
    location: int
    dim_names: str
    expr: str
    children_idx: list[str]

    @property
    def parent(self):
        return self.scop.schedule_tree[self.parent_idx]

    @property
    def children(self):
        return [self.scop.schedule_tree[i] for i in self.children_idx]

    def __repr__(self):
        words = [
            "Node type:",
            f"{self.node_type},",
            f"{self.dim_names},",
            f"{self.expr},",
            f"{self.location}",
        ]
        return " ".join(words)

    def locate(self):
        self.scop.locate(self.location)
        return self.scop.get_current_node_from_ISL(None, None)

    @property
    def avaliable_transformation(self) -> list[Transformation]:
        result = []
        match self.node_type:
            case NodeType.BAND:
                result.append(Transformation.TILE)
                if self.num_children == 1:
                    result.append(Transformation.INTERCHANGE)
        return result

    def transform(self, transformation, *args):
        if transformation not in TRANSFORMATIONS:
            msg = f"{transformation} does not exists"
            raise ValueError(msg)
        tr = TRANSFORMATIONS[transformation]
        if len(args) != len(tr.arg_help):
            raise ValueError("Incorrect number of args!")
        if not tr.valid(self):
            msg = f"Not a valid transformation: {transformation}"
            raise ValueError(msg)
        func = getattr(self.scop.ctadashi, tr.func_name)
        self.scop.locate(self.location)
        return func(self.scop.idx, *args)


class Scop:
    """Single SCoP.

    In the .so file, there is a global `std::vecto` of `isl_scop`
    objects.  Objects of `Scop` (in python) represents a the
    `isl_scop` object by storing its index in the `std::vecto`.

    """

    def __init__(self, idx, ctadashi) -> None:
        self.ctadashi = ctadashi
        self.idx = idx

    def read_dim_names(self):
        # ctadashi return one string for the `dim_names` but there are
        # two layers which need unpacking.
        all_dim_names = self.ctadashi.get_dim_names(self.idx).decode()
        outer_dim_names = all_dim_names.split(";")[:-1]
        return [t.split("|")[:-1] for t in outer_dim_names]

    def make_node(self, parent, location):
        num_children = self.ctadashi.get_num_children(self.idx)
        node = Node(
            scop=self,
            node_type=NodeType(self.ctadashi.get_type(self.idx)),
            num_children=num_children,
            parent_idx=parent,
            location=location,
            dim_names=self.read_dim_names(),
            expr=self.ctadashi.get_expr(self.idx).decode("utf-8"),
            children_idx=[-1] * num_children,
        )
        return node

    def traverse(self, nodes, parent, path):
        node = self.make_node(parent, path)
        current_idx = len(nodes)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                self.ctadashi.goto_child(self.idx, c)
                node.children_idx[c] = len(nodes)
                self.traverse(nodes=nodes, parent=current_idx, path=path + [c])
                self.ctadashi.goto_parent(self.idx)

    @property
    def schedule_tree(self) -> list[Node]:
        self.ctadashi.reset_root(self.idx)
        nodes: list[Node] = []
        self.traverse(nodes, parent=-1, path=[])
        return nodes

    def locate(self, location):
        self.ctadashi.reset_root(self.idx)
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
        self.num_scops = self.ctadashi.get_num_scops(self.source_path_bytes)
        self.scops = [Scop(i, self.ctadashi) for i in range(self.num_scops)]

    def setup_ctadashi(self, app: App):
        os.environ["C_INCLUDE_PATH"] = ":".join(map(str, app.include_paths))
        self.so_path = Path(__file__).parent.parent / "build/libctadashi.so"
        self.check_missing_file(self.so_path)
        self.ctadashi = ctypes.CDLL(str(self.so_path))
        self.ctadashi.get_num_scops.argtypes = [ctypes.c_char_p]
        self.ctadashi.get_num_scops.restype = ctypes.c_int
        self.ctadashi.get_type.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_type.restype = ctypes.c_int
        self.ctadashi.get_num_children.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_num_children.restype = ctypes.c_size_t
        self.ctadashi.goto_parent.argtypes = [ctypes.c_size_t]
        self.ctadashi.goto_child.argtypes = [ctypes.c_size_t, ctypes.c_size_t]
        self.ctadashi.get_expr.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_expr.restype = ctypes.c_char_p
        self.ctadashi.get_dim_names.argtypes = [ctypes.c_size_t]
        self.ctadashi.get_dim_names.restype = ctypes.c_char_p
        self.ctadashi.print_schedule_node.argtypes = [ctypes.c_size_t]
        self.ctadashi.print_schedule_node.restype = None
        self.ctadashi.reset_root.argtypes = [ctypes.c_size_t]
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

    def generate_code(self):
        # rewrite the original source_path file with the generated code
        input_path_bytes = self.get_input_path_bytes_and_backup_source()
        self.ctadashi.generate_code(input_path_bytes, self.source_path_bytes)

    def __len__(self):
        return self.num_scops

    def __getitem__(self, idx):
        return self.scops[idx]

    def __del__(self):
        self.ctadashi.free_scops()
