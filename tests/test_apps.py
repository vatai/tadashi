#!/usr/bin/env python

import unittest
from pathlib import Path

from tadashi import TrEnum, apps


class TestApp(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def compare_members(self, app):
        akeys = sorted(app.__dict__.keys())
        tapp = app.generate_code()
        tkeys = sorted(tapp.__dict__.keys())
        self.assertListEqual(akeys, tkeys)
        not_equal = ["source", "ephemeral", "populate_scops", "scops"]
        for akey, aval in app.__dict__.items():
            tval = tapp.__dict__[akey]
            if akey in not_equal:
                continue
            self.assertEqual((akey, aval), (akey, tval))

    def test_app_legality(self):
        app = apps.Polybench("jacobi-1d")
        trs = [
            [0, 7, TrEnum.SET_LOOP_OPT, 0, 0],
            [0, 2, TrEnum.FULL_SPLIT],
            [0, 7, TrEnum.SET_LOOP_OPT, 0, 3],
        ]
        result = app.transform_list(trs)
        self.assertFalse(result.legal)

    def test_app_legal(self):
        app = apps.Polybench("gemm")
        trs = [
            [1, "full_shift_param", 2, 16],
            [2, "full_fuse"],
            [1, "set_parallel", 6],
            [2, "full_shift_param", 1, 48],
            [2, "tile2d", 32, 32],
            [3, "set_loop_opt", 0, 3],
        ]
        result = app.scops[0].transform_list(trs)

    #     self.assertFalse(result.legal)


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
