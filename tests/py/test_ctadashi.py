#!/usr/bin/env python

import difflib
import tempfile
import unittest
from pathlib import Path

from tadashi.apps import Simple
from tadashi.tadashilib import Scops, Transformation


class TestCtadashi(unittest.TestCase):
    def test_foobar(self):
        app = Simple(source="examples/threeloop.c")
        node_idx = 2
        scops = Scops(app)
        scop = scops[0]  # select_scop()
        node = scop.schedule_tree[node_idx]  # model.select_node(scop)
        node.transform(Transformation.TILE, 4)
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = Path(tmpdir) / self._testMethodName
            outfile_bytes = str(outfile).encode()
            target_code = """#include <stdlib.h>

void f(size_t N, double A[N][N]) {
#pragma scop
  #define min(x,y)    ((x) < (y) ? (x) : (y))
  for(int c0 = 1; c0 < N; c0 += 1)
    for(int c1 = 0; c1 < N; c1 += 4)
      for(int c2 = 0; c2 <= min(3, N - c1 - 1); c2 += 1)
        {
          for(int c3 = 0; c3 < N; c3 += 1)
            A[c0][c1 + c2] = (A[c0][c1 + c2] + (A[c0 - 1][c1 + c2] * (c3)));
          for(int c3 = 0; c3 < N; c3 += 1)
            A[c0][c1 + c2] = ((A[c0][c1 + c2] + A[c0 - 1][c1 + c2]) + (c3));
        }
#pragma endscop
}
""".split(
                "\n"
            )
            scops.ctadashi.generate_code(scops.source_path_bytes, outfile_bytes)
            generated_code = Path(outfile_bytes.decode()).read_text().split("\n")
            # print(target_code)
            diff = difflib.unified_diff(generated_code, target_code)
        diff_str = "\n".join(diff)
        if diff_str:
            print(diff_str)
        self.assertFalse(diff_str)

    def test_lit(self):
        node_idx = 2
        app = Simple(source=Path(__file__).parent.parent / "threeloop.c")
        scops = Scops(app)
        scop = scops[0]  # select_scop()
        node = scop.schedule_tree[node_idx]  # model.select_node(scop)
        node.transform(Transformation.TILE, 4)
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = Path(tmpdir) / self._testMethodName
            outfile_bytes = str(outfile).encode()
            scops.ctadashi.generate_code(scops.source_path_bytes, outfile_bytes)
            generated_code = Path(outfile_bytes.decode()).read_text().split("\n")
        header = "/// TRANSFORM:"
        comment = "///"
        filtered_code = [x for x in generated_code if not x.startswith(comment)]
        target_code = []
        with open(app.source) as file:
            for line in file:
                if line.startswith(header):
                    transform = line.split(header)[1].strip().split(",")
                    # print(f"{transform=}")
                elif line.startswith(comment):
                    stripped_line = line.strip().replace(comment, "")
                    if len(line) > len(comment):
                        stripped_line = stripped_line[1:]
                    target_code.append(stripped_line)
        diff = difflib.unified_diff(filtered_code, target_code)
        diff_str = "\n".join(diff)
        if diff_str:
            print(diff_str)
        self.assertFalse(diff_str)


if __name__ == "__main__":
    print("Hello")
