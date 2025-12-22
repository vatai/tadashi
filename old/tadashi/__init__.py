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

rtd = os.environ.get("READTHEDOCS")

if rtd != "True":
    from ctadashi import ctadashi


@dataclass
class Node:

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


LowerUpperBound = namedtuple(
    "LowerUpperBound",
    ["lower", "upper"],
    defaults=[None, None],
)
"""Integer interval description.

Lower and upper bounds for describing (integer) intervals of valid
arguments for transformations. `None` indicates no upper/lower bound.

"""


def _tilable(node: Node, dim: int) -> bool:
    for _ in range(dim):
        if node.node_type != NodeType.BAND:
            return False
        # if "tile" in node.label and "outer" in node.label:
        #     return False
        node = node.children[0]
    return True


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
    TrEnum.PARTIAL_SHIFT_VAR: PartialShiftVarInfo(),
    TrEnum.PARTIAL_SHIFT_VAL: PartialShiftValInfo(),
    TrEnum.PARTIAL_SHIFT_PARAM: PartialShiftParamInfo(),
    TrEnum.FULL_SHIFT_VAR: FullShiftVarInfo(),
    TrEnum.FULL_SHIFT_VAL: FullShiftValInfo(),
    TrEnum.FULL_SHIFT_PARAM: FullShiftParamInfo(),
    TrEnum.SET_PARALLEL: SetParallelInfo(),
    TrEnum.SET_LOOP_OPT: SetLoopOptInfo(),
}


class Scop:
    """One SCoP in `Scops`, a loop nest (to use a rough analogy).

    In the .so file, there is a global `std::vector` of `isl_scop`
    objects.  Objects of `Scop` (in python) represents a the
    `isl_scop` object by storing its index in the `std::vector`.

    """

    def __init__(self, app_ptr, scop_idx) -> None:
        self.app_ptr = app_ptr
        self.scop_idx = scop_idx

    def get_loop_signature(self):
        """Extract the value for `Node.loop_signature`.

        A "loop signature", contains the information which is relevant
        for the shift transformations.  Loop signature is a list.
        The entries in this list describes the parameters and iteration
        variables of each statement covered by the loop/band node.

        """
        loop_signature = ctadashi.get_loop_signature(self.app_ptr, self.scop_idx)
        return literal_eval(loop_signature)

    def locate(self, location: list[int]):
        """Update the current node on the C/C++ side."""
        ctadashi.goto_root(self.app_ptr, self.scop_idx)
        for c in location:
            ctadashi.goto_child(self.app_ptr, self.scop_idx, c)

    def transform_list(self, trs: list) -> list[bool]:
        result = []
        for node_idx, tr, *args in trs:
            node = self.schedule_tree[node_idx]
            result.append(node.transform(tr, *args))
        return result

    @property
    def legal(self):
        return bool(ctadashi.get_legal(self.app_ptr, self.scop_idx))


class Scops:
    """All SCoPs which belong to a given file.

    The object of type `Scops` is similar to a list."""

    app_ptr: int
    num_scops: int
    scops: list[Scop]

    def __init__(self, source_path: str, defines: list[str]):
        self._check_missing_file(Path(source_path))
        self.defines = defines
        self.app_ptr = ctadashi.init_scops(str(source_path), defines)
        self.num_scops = ctadashi.num_scops(self.app_ptr)
        self.scops = [Scop(self.app_ptr, scop_idx=i) for i in range(self.num_scops)]

    def __del__(self):
        if ctadashi:
            ctadashi.free_scops(self.app_ptr)

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
        ctadashi.generate_code(self.app_ptr, str(input_path), str(output_path))

    def __len__(self):
        return self.num_scops

    def __getitem__(self, idx):
        return self.scops[idx]

    @property
    def legal(self):
        return all(s.legal for s in self.scops)


class LLVMScops(Scops):

    def __init__(self, source_path: Path, compiler: str):
        self._check_missing_file(Path(source_path))
        self.app_ptr = ctadashi.init_scops_from_json(compiler, str(source_path))
        self.num_scops = ctadashi.num_scops(self.app_ptr)
        self.scops = [Scop(self.app_ptr, scop_idx=i) for i in range(self.num_scops)]

    def generate_code(self, input_path, output_path):
        """Generate the source code.

        The transformations happen on the SCoPs (polyhedral
        representations), and to put that into code, this method needs
        to be called.

        """
        ctadashi.generate_code(self.app_ptr, str(input_path), str(output_path))
