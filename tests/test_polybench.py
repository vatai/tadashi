#!/usr/bin/env python

import unittest
from pathlib import Path

from tadashi import TrEnum
from tadashi.apps import Polybench


class TestPolybench(unittest.TestCase):
    base = Path(__file__).parent.parent / "examples/polybench"

    def test_pb_trlist(self):
        app = Polybench("stencils/jacobi-2d", self.base)
        trs = [
            [2, TrEnum.FULL_SPLIT],
            [5, TrEnum.TILE1D, 2],
            [6, TrEnum.TILE1D, 2],
            [5, TrEnum.TILE1D, 4],
            [4, TrEnum.TILE1D, 3],
        ]
        app.scops[0].transform_list(trs)
        mod = app.generate_code()
        mod.compile()
        mod.measure()
