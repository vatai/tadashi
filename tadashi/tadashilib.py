#!/usr/bin/env python

import os
from ctypes import CDLL, c_bool, c_char_p, c_int, c_long, c_size_t
from dataclasses import dataclass
from enum import Enum, StrEnum, auto
from pathlib import Path

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


class Transformation(Enum):
    TILE = "TILE"
    INTERCHANGE = "INTERCHANGE"
    FUSE = "FUSE"
    PARTIAL_SHIFT_VAR = "PARTIAL_SHIFT_VAR"
    PARTIAL_SHIFT_VAL = "PARTIAL_SHIFT_VAL"


class Node:
    def __init__(
        self,
        scop,
        node_type,
        num_children,
        parent,
        location,
        dim_names,
        expr,
    ) -> None:
        self.scop = scop
        self.node_type = NodeType(node_type)
        self.num_children = num_children
        self.parent = parent
        self.dim_names = dim_names
        self.expr = expr.decode("utf-8")
        self.children = [-1] * num_children
        self.location = location

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
        self.scop.locate(self.location)
        match transformation:
            case Transformation.TILE:
                assert len(args) == 1, "Tiling needs exactly 1 argument"
                tile_size = args[0]
                self.scop.tile(tile_size)
            case Transformation.INTERCHANGE:
                assert len(args) == 0, "Interchange needs exactly 0 arguments"
                self.scop.interchange()
            case Transformation.FUSE:
                assert len(args) == 2, "Fuse needs exactly 2 arguments"
                self.scop.fuse(*args)
            case Transformation.PARTIAL_SHIFT_VAR:
                assert len(args) == 2, (
                    "Partial shift id needs exactly 2 args: "
                    "index of the pw aff function, and "
                    "index of the variable/id which should be added."
                )
                self.scop.partial_shift_id(*args)
            case Transformation.PARTIAL_SHIFT_VAL:
                assert len(args) == 2, (
                    "Partial shift val needs exactly 2 args: "
                    "index of the pw aff function, and "
                    "the constant value which should be added."
                )
                self.scop.partial_shift_val(*args)


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
            node_type=self.ctadashi.get_type(self.idx),
            num_children=num_children,
            parent=parent,
            location=location,
            dim_names=self.read_dim_names(),
            expr=self.ctadashi.get_expr(self.idx),
        )
        return node

    def traverse(self, nodes, parent, path):
        node = self.make_node(parent, path)
        current_idx = len(nodes)
        nodes.append(node)
        if not node.node_type == NodeType.LEAF:
            for c in range(node.num_children):
                self.ctadashi.goto_child(self.idx, c)
                node.children[c] = len(nodes)
                self.traverse(nodes, current_idx, path + [c])
                self.ctadashi.goto_parent(self.idx)

    def get_schedule_tree(self) -> list[Node]:
        self.ctadashi.reset_root(self.idx)
        nodes = []
        self.traverse(nodes, parent=-1, path=[])
        return nodes

    def locate(self, location):
        self.ctadashi.reset_root(self.idx)
        for c in location:
            self.ctadashi.goto_child(self.idx, c)

    def tile(self, tile_size):
        self.ctadashi.tile(self.idx, tile_size)

    def interchange(self):
        self.ctadashi.interchange(self.idx)

    def fuse(self, idx1, idx2):
        self.ctadashi.fuse(self.idx, idx1, idx2)

    def partial_shift_id(self, pa_idx, id_idx):
        self.ctadashi.partial_shift_var(self.idx, pa_idx, id_idx)

    def partial_shift_val(self, pa_idx, val):
        self.ctadashi.partial_shift_val(self.idx, pa_idx, val)


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
        os.environ["C_INCLUDE_PATH"] = ":".join(app.include_paths)
        self.so_path = Path(__file__).parent.parent / "build/libctadashi.so"
        self.check_missing_file(self.so_path)
        self.ctadashi = CDLL(str(self.so_path))
        self.ctadashi.get_num_scops.argtypes = [c_char_p]
        self.ctadashi.get_num_scops.restype = c_int
        self.ctadashi.get_type.argtypes = [c_size_t]
        self.ctadashi.get_type.restype = c_int
        self.ctadashi.get_num_children.argtypes = [c_size_t]
        self.ctadashi.get_num_children.restype = c_size_t
        self.ctadashi.goto_parent.argtypes = [c_size_t]
        self.ctadashi.goto_child.argtypes = [c_size_t, c_size_t]
        self.ctadashi.get_expr.argtypes = [c_size_t]
        self.ctadashi.get_expr.restype = c_char_p
        self.ctadashi.get_dim_names.argtypes = [c_size_t]
        self.ctadashi.get_dim_names.restype = c_char_p
        self.ctadashi.get_schedule_yaml.argtypes = [c_size_t]
        self.ctadashi.get_schedule_yaml.restype = c_char_p
        self.ctadashi.reset_root.argtypes = [c_size_t]
        # Transformations
        self.ctadashi.tile.argtypes = [c_size_t, c_size_t]
        self.ctadashi.tile.restype = c_bool
        self.ctadashi.interchange.argtypes = [c_size_t]
        self.ctadashi.interchange.restype = c_bool
        self.ctadashi.tile.argtypes = [c_size_t, c_int, c_int]
        self.ctadashi.tile.restype = c_bool
        self.ctadashi.partial_shift_var.argtypes = [c_size_t, c_int, c_long]
        self.ctadashi.partial_shift_var.restype = c_bool
        self.ctadashi.partial_shift_val.argtypes = [c_size_t, c_int, c_long]
        self.ctadashi.partial_shift_val.restype = c_bool
        #
        self.ctadashi.generate_code.argtypes = [c_char_p, c_char_p]

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
