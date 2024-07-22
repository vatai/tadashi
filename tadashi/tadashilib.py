#!/usr/bin/env python

# from ctypes import CDLL, c_bool, c_char_p, c_int, c_long, c_size_t
from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from enum import Enum, auto
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


class Transformation(Enum):
    TILE = "TILE"
    INTERCHANGE = "INTERCHANGE"
    FUSE = "FUSE"
    FULL_FUSE = "FULL_FUSE"
    PARTIAL_SHIFT_VAR = "PARTIAL_SHIFT_VAR"
    PARTIAL_SHIFT_VAL = "PARTIAL_SHIFT_VAL"
    FULL_SHIFT_VAR = "FULL_SHIFT_VAR"
    FULL_SHIFT_VAL = "FULL_SHIFT_VAL"
    FULL_SHIFT_PARAM = "FULL_SHIFT_PARAM"
    PARTIAL_SHIFT_PARAM = "PARTIAL_SHIFT_PARAM"
    PRINT_SCHEDULE = "PRINT_SCHEDULE"
    SET_LOOP_OPT = "SET_LOOP_OPT"


TRANSFORMATIONS = {
    Transformation.TILE: TransformationInfo(
        func_name="tile",
        argtypes=[ctypes.c_size_t],
        arg_help=["Tile size"],
        restype=ctypes.c_bool,
        valid=lambda t: t.node_type == NodeType.BAND,
    ),
    Transformation.INTERCHANGE: TransformationInfo(
        func_name="interchange",
        argtypes=[],
        arg_help=[],
        restype=ctypes.c_bool,
        valid=lambda t: t.node_type == NodeType.BAND
        and len(t.children) == 1
        and t.children[0].node_type == NodeType.BAND,
    ),
    Transformation.FUSE: TransformationInfo(
        func_name="fuse",
        argtypes=[ctypes.c_int, ctypes.c_int],
        arg_help=["Index of first loop to fuse", "Index of second loop to fuse"],
        restype=ctypes.c_bool,
        valid=lambda t: t.node_type == NodeType.SEQUENCE,
    ),
}
# self.ctadashi.fuse.argtypes = [c_size_t, c_int, c_int]
# self.ctadashi.fuse.restype = c_bool
# self.ctadashi.full_fuse.argtypes = [c_size_t]
# self.ctadashi.full_fuse.restype = c_bool
# self.ctadashi.partial_shift_var.argtypes = [c_size_t, c_int, c_long, c_long]
# self.ctadashi.partial_shift_var.restype = c_bool
# self.ctadashi.partial_shift_val.argtypes = [c_size_t, c_int, c_long]
# self.ctadashi.partial_shift_val.restype = c_bool
# self.ctadashi.full_shift_var.argtypes = [c_size_t, c_long, c_long]
# self.ctadashi.full_shift_var.restype = c_bool
# self.ctadashi.full_shift_val.argtypes = [c_size_t, c_long]
# self.ctadashi.full_shift_val.restype = c_bool
# self.ctadashi.set_loop_opt.argtypes = [c_size_t, c_int, c_int]
# self.ctadashi.set_loop_opt.restype = None
# self.ctadashi.full_shift_param.argtypes = [c_size_t, c_long, c_long]
# self.ctadashi.full_shift_param.restype = c_bool
# self.ctadashi.partial_shift_param.argtypes = [c_size_t, c_int, c_long, c_long]
# self.ctadashi.partial_shift_param.restype = c_bool


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
            raise ValueError
        tr = TRANSFORMATIONS[transformation]
        if len(args) != len(tr.arg_help):
            raise ValueError("Incorrect number of args!")
        func = getattr(self.scop.ctadashi, tr.func_name)
        self.scop.locate(self.location)
        return func(self.scop.idx, *args)

    def transform_(self, transformation, *args):
        self.scop.locate(self.location)
        # info = dict[transformation]
        # func = info["func"]
        # num_args = len(func.arglist) - 1
        # if len(args) != num_args:
        #   assert num_args == len(info["args help"])
        #   printf(f"Transfomation {transfomation} takes exactly {num_args} number of arguments!")
        #   assert num_
        match transformation:
            case Transformation.TILE:
                assert len(args) == 1, "Tiling needs exactly 1 argument"
                fun = self.scop.ctadashi.tile
                return self.call_ctadashi(fun, *args)
            case Transformation.INTERCHANGE:
                assert len(args) == 0, "Interchange needs exactly 0 arguments"
                fun = self.scop.ctadashi.interchange
                return self.call_ctadashi(fun)
            case Transformation.FUSE:
                assert len(args) == 2, "Fuse needs exactly 2 arguments"
                fun = self.scop.ctadashi.fuse
                return self.call_ctadashi(fun, *args)
            case Transformation.FULL_FUSE:
                assert len(args) == 0, "Fuse needs exactly 0 arguments"
                fun = self.scop.ctadashi.full_fuse
                return self.call_ctadashi(fun, *args)
            case Transformation.PARTIAL_SHIFT_VAR:
                assert len(args) == 3, (
                    "Partial shift id needs exactly 2 args: "
                    "index of the loop, and "
                    "index of the variable/id which should be added."
                )
                fun = self.scop.ctadashi.partial_shift_var
                return self.call_ctadashi(fun, *args)
            case Transformation.PARTIAL_SHIFT_VAL:
                assert len(args) == 2, (
                    "Partial shift val needs exactly 2 args: "
                    "index of the loop, and "
                    "the constant value which should be added."
                )
                fun = self.scop.ctadashi.partial_shift_val
                return self.call_ctadashi(fun, *args)
            case Transformation.FULL_SHIFT_VAR:
                assert len(args) == 2, (
                    "Full shift id needs exactly 1 args: "
                    "index of the variable/id which should be added."
                )
                fun = self.scop.ctadashi.full_shift_var
                return self.call_ctadashi(fun, *args)
            case Transformation.FULL_SHIFT_VAL:
                assert len(args) == 1, (
                    "Full shift val needs exactly 1 args: "
                    "the constant value which should be added."
                )
                fun = self.scop.ctadashi.full_shift_val
                return self.call_ctadashi(fun, *args)
            case Transformation.FULL_SHIFT_PARAM:
                assert len(args) == 2, (
                    "Partial shift param needs exactly 1 args: "
                    "the index of the param which should be added."
                )
                fun = self.scop.ctadashi.full_shift_param
                return self.call_ctadashi(fun, *args)
            case Transformation.PARTIAL_SHIFT_PARAM:
                assert len(args) == 3, (
                    "Partial shift param needs exactly 2 args: "
                    "index of the loop, and "
                    "the index of the param which should be added."
                )
                fun = self.scop.ctadashi.partial_shift_param
                return self.call_ctadashi(fun, *args)
            case Transformation.PRINT_SCHEDULE:
                fun = self.scop.ctadashi.print_schedule_node
                return self.call_ctadashi(fun, *args)
            case Transformation.SET_LOOP_OPT:
                fun = self.scop.ctadashi.set_loop_opt
                return self.call_ctadashi(fun, *args)
            case _:
                msg = "Odd?! Looks like the developer didn't cover all cases!"
                raise ValueError(msg)

    def call_ctadashi(self, fun, *args):
        if len(args) != len(fun.argtypes) - 1:
            raise ValueError("Incorrect number of args!")
        return fun(self.scop.idx, *args)


class Scop:
    """Single SCoP.

    In the .so file, there is a global `std::vecto` of `isl_scop`
    objects.  Objects of `Scop` (in python) represents a the
    `isl_scop` object by storing its index in the `std::vecto`.

    """

    def __init__(self, idx, ctadashi) -> None:
        self.ctadashi = ctadashi
        self.idx = idx
        self.schedule_tree = self.get_schedule_tree()

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

    def get_schedule_tree(self) -> list[Node]:
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
            msg = f"The transfomation {tr_name} is not specified correctly!"
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
