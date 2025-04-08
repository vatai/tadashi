#!/usr/bin/env python

import unittest
from pathlib import Path

from tadashi import TrEnum
from tadashi.apps import Simple


class TestTadashi(unittest.TestCase):
    def test_get_args(self):
        app = Simple(Path(__file__).parent.parent / "examples/inputs/shifts.c")
        node = app.scops[0].schedule_tree[3]
        tr = TrEnum.PARTIAL_SHIFT_VAR
        avail_args = node.available_args(tr)
        args = node.get_args(tr, -3, 2)
        self.assertEqual(len(avail_args[0]) * 5, len(args))
