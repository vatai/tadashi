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
        TRANSFORMATION = " TRANSFORMATION: "
        if line.startswith(COMMENT):
            stripped_line = line.strip().replace(COMMENT, "")
            if stripped_line.startswith(TRANSFORMATION):
                transform_str = stripped_line.replace(TRANSFORMATION, "")
                evaled = ast.literal_eval(transform_str)
                transform_data.scop_idx = evaled[0]
                transform_data.node_idx = evaled[1]
                transform_data.transformation = Transformation(evaled[2])
                transform_data.transformation_args = evaled[3:]
                return True
            else:
                target_line = stripped_line[1:] if stripped_line else stripped_line
                target_code.append(target_line)
        return False

    @classmethod
    def _read_app_comments(cls, app):
        transforms = []
        target_code = []
        transform_data = TransformData()
        with open(app.source) as file:
            for line in file:
                if cls._proc_line(line, transform_data, target_code):
                    transforms.append(transform_data)
        return transforms, target_code

    def _get_filtered_code(self, scops):
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = Path(tmpdir) / self._testMethodName
            outfile_bytes = str(outfile).encode()
            scops.ctadashi.generate_code(scops.source_path_bytes, outfile_bytes)
            generated_code = Path(outfile_bytes.decode()).read_text().split("\n")
        return [x for x in generated_code if not x.startswith(COMMENT)]

    def _lit(self, app):
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
        app = Simple(source=Path(__file__).parent.parent / "threeloop.c")
        self._lit(app)


if __name__ == "__main__":
    print("Hello")
