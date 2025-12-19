#!/bin/env python

import unittest
from pathlib import Path

from tadashi import apps
from tadashi.scop import TrEnum
from tadashi.translators import Pet


class TestApp(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def compare_members(self, app):
        akeys = sorted(app.__dict__.keys())
        tapp = app.generate_code(ensure_legality=False)
        tkeys = sorted(tapp.__dict__.keys())
        self.assertListEqual(akeys, tkeys)
        not_equal = ["source", "ephemeral", "populate_scops", "translator"]
        for akey, aval in app.__dict__.items():
            tval = tapp.__dict__[akey]
            if akey in not_equal:
                continue
            self.assertEqual((akey, aval), (akey, tval))

    @unittest.skip("todo")
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
            [2, "tile_2d", 32, 32],
            [3, "set_loop_opt", 0, 3],
        ]
        result = app.scops[0].transform_list(trs)
        app.reset_scops()
        for legal, (ni, *args) in zip(result, trs):
            node = app.scops[0].schedule_tree[ni]
            rv = node.transform(*args)
            self.assertEqual(rv, legal)
            self.assertEqual(rv, app.legal)


class TestSimple(TestApp):
    def test_generate_code_ephemeral(self):
        """Test the `generate_code`s method `ephemeral` parameter."""
        input_file = self.examples / "inputs/depnodep.c"
        for ephemeral in [True, False]:
            expected = not ephemeral
            with self.subTest(ephemeral=ephemeral):
                app = apps.Simple(input_file, Pet())
                tapp = app.generate_code(ensure_legality=False, ephemeral=ephemeral)
                file_path = tapp.source
                del tapp
                file_exists = file_path.exists()
                if file_exists:
                    file_path.unlink()
                self.assertEqual(file_exists, expected)

    def test_args(self):
        file = self.examples / "inputs/depnodep.c"
        app = apps.Simple(file, Pet(autodetect=True))
        self.compare_members(app)


class TestPolybench(TestApp):
    base: Path = TestApp.examples / "polybench"

    @unittest.skip("wip")
    def test_args(self):
        app = apps.Polybench("stencils/jacobi-2d", self.base)
        self.compare_members(app)

    @unittest.skip("wip")
    def test_trlist(self):
        app = apps.Polybench("stencils/jacobi-2d", self.base)
        trs = [
            [2, TrEnum.FULL_SPLIT],
            [3, TrEnum.TILE_2D, 20, 20],
            [10, TrEnum.TILE_3D, 30, 30, 30],
        ]
        app.scops[0].transform_list(trs)
        tapp = app.generate_code(ensure_legality=False)
        tapp.compile()
        # tapp.measure()

    @unittest.skip("wip")
    def test_get_benchmark(self):
        app = apps.Polybench("correlation")
        self.assertEqual(app.benchmark, "datamining/correlation")

        app = apps.Polybench("datamining/correlation")  # old
        self.assertEqual(app.benchmark, "datamining/correlation")

        with self.assertRaises(ValueError):
            app = apps.Polybench("polybench")  # special case

        with self.assertRaises(ValueError):
            app = apps.Polybench("does_not_exist")

    @unittest.skip("wip")
    def test_dump_arrays(self):
        # print([a.name for a in apps.Polybench.get_benchmarks()])
        app = apps.Polybench("deriche", compiler_options=["-DMINI_DATASET"])
        # for idx, node in enumerate(app.scops[0].schedule_tree):
        #     if TrEnum.SPLIT in node.available_transformations:
        #         print(f"node[{idx}] has SPLI")
        # print(node.yaml_str)
        node = app.scops[0].schedule_tree[20]
        node.transform(TrEnum.SPLIT, 1)
        tapp = app.generate_code()
        tarrays = tapp.dump_arrays()
        tapp.measure()
