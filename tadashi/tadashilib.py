#!/usr/bin/env python

import os
from ctypes import CDLL, c_char_p, c_int, c_size_t
from enum import Enum, auto
from pathlib import Path

from apps import App


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
    TILE = 0


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
        match self.node_type:
            case NodeType.BAND:
                return [Transformation.TILE]
        return []

    def transform(self, transformation, *args):
        self.scop.locate(self.location)
        match transformation:
            case Transformation.TILE:
                assert len(args) == 1, "Tiling needs exactly one argument"
                tile_size = args[0]
                self.scop.tile(tile_size)


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
        self.ctadashi.get_type_str.argtypes = [c_size_t]
        self.ctadashi.get_type_str.restype = c_char_p
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
        self.ctadashi.tile.argtypes = [c_size_t, c_size_t]
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
