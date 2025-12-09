#!/bin/env python

import unittest
from pathlib import Path

from tadashi.translators import Pet


class TestScop(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def test_scop_schedule_tree(self):
        """Test the `translators.Pet`'s `autodetect` parameter."""
        file = self.examples / "inputs/depnodep.c"
        translator = Pet()
        translator.set_source(file)
        scop = translator.scops[0]
        self.assertEqual(len(scop.schedule_tree), 4)
        for node in scop.schedule_tree:
            print(f"{node.expr=}")
            print(f"{node.node_type=}")
