#!/usr/bin/env python
import ast
import difflib
import logging
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import tadashi
from tadashi import TrEnum
from tadashi.apps import Polybench, Simple
from tadashi.translators import Pet

HEADER = "/// TRANSFORMATION: "
COMMENT = "///"


@dataclass
class TransformData:
    scop_idx: int = -1
    node_idx: int = -1
    transformation: Optional[TrEnum] = None
    transformation_args: list[int] = field(default_factory=list)


def get_inputs_path() -> Path:
    base = Path(__file__).parent.parent
    return base / "examples/inputs"


class TestCcScop(unittest.TestCase):
    @staticmethod
    def _read_app_comments(app):
        TRANSFORMATION = " TRANSFORMATION: "
        transforms = []
        target_code = []
        with open(app.source) as file:
            for commented_line in file:
                if not commented_line.startswith(COMMENT):
                    continue
                line = commented_line.strip().replace(COMMENT, "")
                if line.startswith(TRANSFORMATION):
                    transform_str = line.replace(TRANSFORMATION, "")
                    lits = ast.literal_eval(transform_str)
                    td = TransformData(*lits[:2], TrEnum(lits[2].lower()), lits[3:])
                    transforms.append(td)
                else:
                    target_line = line[1:] if line else line
                    target_code.append(target_line)
        return transforms, target_code

    def _get_generated_code(self, app: Simple):
        tapp = app.generate_code(ensure_legality=False)
        generated_code = tapp.source.read_text().split("\n")
        return [x for x in generated_code if not x.startswith(COMMENT)]

    def check(self, app_file):
        logger = logging.getLogger(self._testMethodName)
        app = Simple(app_file, Pet())
        transforms, target_code = self._read_app_comments(app)

        # transform
        logger.info("Start test")
        legality = []
        for tr in transforms:
            scop = app.scops[tr.scop_idx]  # select_scop()
            node = scop.schedule_tree[tr.node_idx]  # model.select_node(scop)
            legal = node.transform(tr.transformation, *tr.transformation_args)
            if legal is not None:
                legality.append(f"legality={legal}")

        logger.info("Transformations done")
        generated_code = self._get_generated_code(app)
        logger.info("Code generated")
        generated_code += legality
        diff = difflib.unified_diff(generated_code, target_code)
        diff_str = "\n".join(diff)
        if diff_str:
            print(f"\n{Path(__file__).parent/self._testMethodName}.c:1:1")
            print(diff_str)
        logger.info("Test finished")
        del app
        self.assertTrue(generated_code == target_code)

    @staticmethod
    def _get_node(idx):
        app = Simple("tests/dummy.c", Pet())
        node = app.scops[0].schedule_tree[idx]
        return node

    @classmethod
    def _get_band_node(cls):
        return cls._get_node(1)

    @classmethod
    def _get_sequence_node(cls):
        return cls._get_node(3)

    def test_wrong_number_of_args(self):
        node = self._get_band_node()
        self.assertRaises(ValueError, node.transform, TrEnum.TILE_1D, 2, 3)

    def test_transformation_list(self):
        app = Simple("examples/inputs/depnodep.c", Pet())
        scop = app.scops[0]
        transformations = [
            [2, tadashi.TrEnum.SET_PARALLEL, 1],
            [1, tadashi.TrEnum.SET_LOOP_OPT, 0, 3],
            [1, tadashi.TrEnum.FULL_SHIFT_VAL, -47],
            [3, tadashi.TrEnum.PARTIAL_SHIFT_VAL, 0, 39],
            [1, tadashi.TrEnum.PARTIAL_SHIFT_VAL, 0, 34],
            [3, tadashi.TrEnum.PARTIAL_SHIFT_VAR, 0, 0, -22],
            [3, tadashi.TrEnum.SET_PARALLEL, 1],
        ]
        legals = scop.transform_list(transformations)
        mod_app = app.generate_code(ensure_legality=False)
        mod_app.compile()
        for legal in legals[:-1]:
            self.assertTrue(legal)
        self.assertFalse(legals[-1])

    def test_labels(self):
        app = Polybench(Path("correlation"))
        self.assertEqual(app.scops[0].schedule_tree[27].label, "L_4")
        trs = [[27, TrEnum.TILE_1D, 11]]
        app.scops[0].transform_list(trs)
        self.assertEqual(app.scops[0].schedule_tree[27].label, "L_4-tile1d-outer")
        self.assertEqual(app.scops[0].schedule_tree[28].label, "L_4-tile1d-inner")

        app.scops[0].reset()
        trs = [[27, TrEnum.TILE_2D, 11, 13]]
        app.scops[0].transform_list(trs)
        self.assertEqual(app.scops[0].schedule_tree[27].label, "L_4-tile2d-outer")
        self.assertEqual(app.scops[0].schedule_tree[28].label, "L_5-tile2d-outer")

    def test_repeated_code_generation(self):
        base = Path(__file__).parent.parent
        app = Simple(base / "examples/inputs/simple/two_loops.c", Pet())
        node = app.scops[0].schedule_tree[1]
        node.transform(TrEnum.TILE_2D, 12, 4)
        for i in range(30):
            app = app.generate_code(populate_scops=True)

    def test_bad_deps(self):
        app = Simple("tests/bad_deps.c", Pet())
        scop = app.scops[0]
        node = scop.schedule_tree[1]
        # print(node.yaml_str)
        trs = [[2, TrEnum.FULL_SPLIT]]
        valid = scop.transform_list(trs)
        tapp = app.generate_code(ensure_legality=False)
        # print(f"{valid=}")
        # print(tapp.source.read_text())

    def test_legality_new(self):
        app = Polybench("gemm")
        self.assertTrue(app.legal)


class TestCtadashiLLVM(unittest.TestCase):
    @unittest.skip("wip llvm")
    def test_foobar(self):
        # app = Polybench("gemm")
        app = tadashi.apps.SimpleLLVM(get_inputs_path() / "depnodep.c", Pet())
        print(app.source.exists())
        # node = app.scops[0].schedule_tree[2]
        node = app.scops[0].schedule_tree[1]
        # print(node.yaml_str)
        # tr = [tadashi.TrEnum.FULL_SPLIT]
        tr = [TrEnum.TILE2D, 3, 3]
        legal = node.transform(*tr)
        # print(node.yaml_str)
        tapp = app.generate_code()
        print(f"{legal=}")
        self.assertTrue(True)


def setup():
    if "-v" in sys.argv:
        logging.basicConfig(level=logging.INFO)
    test_dir = Path(__file__).parent
    for app_path in test_dir.glob("test_*.c"):

        def ch(app_path):
            return lambda self: self.check(app_path)

        test_name = app_path.with_suffix("").name
        setattr(TestCcScop, test_name, ch(app_path))


setup()
