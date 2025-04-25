#!/usr/bin/env python

import unittest
from pathlib import Path

from tadashi import TrEnum, apps


class TestApp(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def compare_members(self, app):
        a = sorted(app.__dict__.keys())
        tapp = app.generate_code()
        t = sorted(tapp.__dict__.keys())
        self.assertListEqual(a, t)


class TestSimple(TestApp):
    def test_args(self):
        app = apps.Simple(self.examples / "inputs/depnodep.c")
        self.compare_members(app)


class TestPolybench(TestApp):
    base: Path = TestApp.examples / "polybench"

    def test_args(self):
        app = apps.Polybench("stencils/jacobi-2d", self.base)
        self.compare_members(app)

    def test_trlist(self):
        app = apps.Polybench("stencils/jacobi-2d", self.base)
        trs = [
            [2, TrEnum.FULL_SPLIT],
            [3, TrEnum.TILE2D, 20, 20],
            [10, TrEnum.TILE3D, 30, 30, 30],
        ]
        app.scops[0].transform_list(trs)
        mod = app.generate_code()
        mod.compile()
        # mod.measure()

    def test_get_benchmark(self):
        app = apps.Polybench("correlation")
        self.assertEqual(app.benchmark, "datamining/correlation")

        app = apps.Polybench("datamining/correlation")  # old
        self.assertEqual(app.benchmark, "datamining/correlation")

        with self.assertRaises(ValueError):
            app = apps.Polybench("polybench")  # special case

        with self.assertRaises(ValueError):
            app = apps.Polybench("does_not_exist")
