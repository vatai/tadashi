#!/bin/env python

import unittest
from pathlib import Path

from tadashi.translators import Pet


class TestScop(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def test_pet_autodetect(self):
        """Test the `translators.Pet`'s `autodetect` parameter."""
        file = self.examples / "inputs/depnodep.c"
        translator = Pet()
        translator.set_source(file)
        scop = translator.scops[0]
        node = scop.schedule_tree[0]
