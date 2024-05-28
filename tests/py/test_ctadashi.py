#!/usr/bin/env python

import ast
import difflib
import tempfile
import unittest
from pathlib import Path

from tadashi.apps import Simple
from tadashi.tadashilib import Scops, Transformation

HEADER = "/// TRANSFORMATION: "
COMMENT = "///"


def foobar(app):
    target_code = []
    with open(app.source) as file:
        for line in file:
            if line.startswith(HEADER):
                transform_str = line.split(HEADER)[1].strip().split(",")
            elif line.startswith(COMMENT):
                stripped_line = line.strip().replace(COMMENT, "")
                if len(line) > len(COMMENT):
                    stripped_line = stripped_line[1:]
                target_code.append(stripped_line)
    print(transform_str)
    # transform = ast.literal_eval(transform_str)
    # print(transform)
    return target_code


class TestCtadashi(unittest.TestCase):
    def test_lit(self):
        app = Simple(source=Path(__file__).parent.parent / "threeloop.c")
        target_code = foobar(app)

        # transform
        scop_idx = 0
        node_idx = 2
        scops = Scops(app)
        scop = scops[scop_idx]  # select_scop()
        node = scop.schedule_tree[node_idx]  # model.select_node(scop)
        node.transform(Transformation.TILE, 4)

        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = Path(tmpdir) / self._testMethodName
            outfile_bytes = str(outfile).encode()
            scops.ctadashi.generate_code(scops.source_path_bytes, outfile_bytes)
            generated_code = Path(outfile_bytes.decode()).read_text().split("\n")
        filtered_code = [x for x in generated_code if not x.startswith(COMMENT)]
        diff = difflib.unified_diff(filtered_code, target_code)
        diff_str = "\n".join(diff)
        if diff_str:
            print(diff_str)
        self.assertFalse(diff_str)


if __name__ == "__main__":
    print("Hello")
