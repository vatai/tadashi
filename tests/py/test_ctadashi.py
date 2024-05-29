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


def foobar(app):
    target_code = []
    with open(app.source) as file:
        for line in file:
            if line.startswith(HEADER):
                transform_str = line.replace(HEADER, "")
            elif line.startswith(COMMENT):
                stripped_line = line.strip().replace(COMMENT, "")
                if len(line) > len(COMMENT):
                    stripped_line = stripped_line[1:]
                target_code.append(stripped_line)
    transform = list(ast.literal_eval(transform_str))
    transform_and_args = [Transformation(transform[0])] + transform[1:]
    return transform_and_args, target_code


def proc_line(line: str, transform_data: TransformData, target_code: list[str]):
    TRANSFORMATION = "TRANSFORMATION: "
    SCOP_IDX = "SCOP_IDX: "
    NODE_IDX = "NODE_IDX: "
    if line.startswith(COMMENT):
        no_comment_line = line.replace(COMMENT, "")
        if not no_comment_line:
            return False
        # if no_comment_line[0] != " ":
        #     raise ValueError("In correctly formatted line")
        stripped_line = no_comment_line[1:]
        if stripped_line.startswith(TRANSFORMATION):
            evaled = ast.literal_eval(stripped_line.replace(TRANSFORMATION, ""))
            transform_data.transformation = Transformation(evaled[0])
            transform_data.transformation_args = evaled[1:]
            return True
        elif stripped_line.startswith(SCOP_IDX):
            return False
        elif stripped_line.startswith(NODE_IDX):
            return False

    return False


def foobar2(app):
    results = []
    target_code = []
    transform_data = TransformData()
    print(f"{transform_data=}")
    with open(app.source) as file:
        for line in file:
            if proc_line(line, transform_data, target_code):
                results.append(transform_data)
                transform_data = TransformData()
    print(f"{transform_data=}")
    return results


class TestCtadashi(unittest.TestCase):
    def get_filtered_code(self, scops):
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = Path(tmpdir) / self._testMethodName
            outfile_bytes = str(outfile).encode()
            scops.ctadashi.generate_code(scops.source_path_bytes, outfile_bytes)
            generated_code = Path(outfile_bytes.decode()).read_text().split("\n")
        return [x for x in generated_code if not x.startswith(COMMENT)]

    def test_lit(self):
        app = Simple(source=Path(__file__).parent.parent / "threeloop.c")
        transform_with_args, target_code = foobar(app)
        foobar2(app)

        # transform
        scop_idx = 0
        node_idx = 2
        scops = Scops(app)
        scop = scops[scop_idx]  # select_scop()
        node = scop.schedule_tree[node_idx]  # model.select_node(scop)
        node.transform(*transform_with_args)

        filtered_code = self.get_filtered_code(scops)
        diff = difflib.unified_diff(filtered_code, target_code)
        diff_str = "\n".join(diff)
        if diff_str:
            print(diff_str)
        self.assertFalse(diff_str)


if __name__ == "__main__":
    print("Hello")
