#!/usr/bin/env python
import ast
import difflib
import logging
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from tadashi.apps import Simple
from tadashi.tadashilib import Scops, Transformation

HEADER = "/// TRANSFORMATION: "
COMMENT = "///"


@dataclass
class TransformData:
    scop_idx: int = -1
    node_idx: int = -1
    transformation: Optional[Transformation] = None
    transformation_args: list[int] = field(default_factory=list)


class TestCtadashi(unittest.TestCase):
    @staticmethod
    def _proc_line(line: str, transform_data: TransformData, target_code: list[str]):
        """Return `True` if the line contains transformation data.

        Return `True` when the `transform_data` object gets populated, and
        `False` when the line is appended to the `target_code` list.

        """
        return False

    @classmethod
    def _read_app_comments(cls, app):
        TRANSFORMATION = " TRANSFORMATION: "
        transforms = []
        target_code = []
        transform_data = TransformData()
        with open(app.source) as file:
            for commented_line in file:
                if not commented_line.startswith(COMMENT):
                    continue
                line = commented_line.strip().replace(COMMENT, "")
                if line.startswith(TRANSFORMATION):
                    transform_str = line.replace(TRANSFORMATION, "")
                    lits = ast.literal_eval(transform_str)
                    td = TransformData(
                        *lits[:2], Transformation(lits[2].lower()), lits[3:]
                    )
                    transforms.append(td)
                else:
                    target_line = line[1:] if line else line
                    target_code.append(target_line)
        return transforms, target_code

    def _get_generated_code(self, scops):
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = Path(tmpdir) / self._testMethodName
            outfile_bytes = str(outfile).encode()
            scops.ctadashi.generate_code(scops.source_path_bytes, outfile_bytes)
            generated_code = Path(outfile_bytes.decode()).read_text().split("\n")
        return [x for x in generated_code if not x.startswith(COMMENT)]

    def check(self, app_file):
        logger = logging.getLogger(self._testMethodName)
        app = Simple(source=app_file)
        transforms, target_code = self._read_app_comments(app)

        # transform
        scops = Scops(app)
        logger.info("Start test")
        legality = []
        for tr in transforms:
            scop = scops[tr.scop_idx]  # select_scop()
            node = scop.schedule_tree[tr.node_idx]  # model.select_node(scop)
            legal = node.transform(tr.transformation, *tr.transformation_args)
            if legal is not None:
                legality.append(f"legality={legal}")

        logger.info("Transformations done")
        generated_code = self._get_generated_code(scops)
        logger.info("Code generated")
        generated_code += legality
        diff = difflib.unified_diff(generated_code, target_code)
        diff_str = "\n".join(diff)
        if diff_str:
            print(f"\n{Path(__file__).parent/self._testMethodName}.c:1:1")
            print(diff_str)
        logger.info("Test finished")
        del scops
        self.assertTrue(generated_code == target_code)

    @staticmethod
    def _get_node(idx):
        app = Simple("tests/py/dummy.c")
        scops = Scops(app)
        node = scops[0].schedule_tree[idx]
        return node

    @classmethod
    def _get_band_node(cls):
        return cls._get_node(1)

    @classmethod
    def _get_sequence_node(cls):
        return cls._get_node(3)

    def test_wrong_number_of_args(self):
        node = self._get_band_node()
        self.assertRaises(ValueError, node.transform, Transformation.TILE, 2, 3)

    def test_nonexisting_transformation(self):
        node = self._get_band_node()
        self.assertRaises(ValueError, node.transform, None)


def setup():
    if "-v" in sys.argv:
        logging.basicConfig(level=logging.INFO)
    test_dir = Path(__file__).parent
    for app_path in test_dir.glob("test_*.c"):

        def ch(app_path):
            return lambda self: self.check(app_path)

        test_name = app_path.with_suffix("").name
        setattr(TestCtadashi, test_name, ch(app_path))


setup()
