#!/usr/bin/env python

import unittest
from pathlib import Path

from tadashi import TrEnum
from tadashi.apps import Polybench, Simple


class TestTadashi(unittest.TestCase):
    def test_get_args(self):
        app = Simple(Path(__file__).parent.parent / "examples/inputs/shifts.c")
        node = app.scops[0].schedule_tree[3]
        tr = TrEnum.PARTIAL_SHIFT_VAR
        avail_args = node.available_args(tr)
        start, end = -3, 2
        args = node.get_args(tr, start, end)
        node.transform(tr, *args[0])
        # args have `end - start` selections for the last dim, which
        # is an infinite interval...
        self.assertEqual(len(avail_args[0]) * (end - start), len(args))

    def test_scop_legality(self):
        app = Polybench("jacobi-1d")
        trs = [
            [7, TrEnum.SET_LOOP_OPT, 0, 0],
            [2, TrEnum.FULL_SPLIT],
            [7, TrEnum.SET_LOOP_OPT, 0, 3],
        ]
        legal = app.scops[0].transform_list(trs)
        self.assertTrue(legal[0])
        self.assertFalse(legal[1])
        self.assertFalse(legal[2])
