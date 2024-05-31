#!/usr/bin/env python

import ast
import difflib
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
                    td = TransformData(*lits[:2], Transformation(lits[2]), lits[3:])
                    transforms.append(td)
                else:
                    target_line = line[1:] if line else line
                    target_code.append(target_line)
        return transforms, target_code

    def _get_filtered_code(self, scops):
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = Path(tmpdir) / self._testMethodName
            outfile_bytes = str(outfile).encode()
            scops.ctadashi.generate_code(scops.source_path_bytes, outfile_bytes)
            generated_code = Path(outfile_bytes.decode()).read_text().split("\n")
        return [x for x in generated_code if not x.startswith(COMMENT)]

    def _lit(self, app_file):
        app = Simple(source=app_file)
        transforms, target_code = self._read_app_comments(app)

        # transform
        scops = Scops(app)
        for transform in transforms:
            scop = scops[transform.scop_idx]  # select_scop()
            node = scop.schedule_tree[transform.node_idx]  # model.select_node(scop)
            node.transform(transform.transformation, *transform.transformation_args)

        filtered_code = self._get_filtered_code(scops)
        diff = difflib.unified_diff(filtered_code, target_code)
        diff_str = "\n".join(diff)
        if diff_str:
            print(diff_str)
        self.assertFalse(diff_str)

    def test_threeloop(self):
        test_dir = Path(__file__).parent.parent
        for app_path in test_dir.glob("*.c"):
            self._lit(app_path)


if __name__ == "__main__":
    print("Hello")
