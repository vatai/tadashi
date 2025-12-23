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
    @staticmethod
    def _check_missing_file(path: Path):
        if not path.exists():
            raise ValueError(f"{path} does not exist!")
