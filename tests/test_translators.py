#!/bin/env python

import unittest
from pathlib import Path

from tadashi.translators import *


class TestTranslator(unittest.TestCase):
    """!!! Consider other functionality. Also consider testing ccscop
    functionality.

    """

    examples: Path = Path(__file__).parent.parent / "examples"

    def test_pet_autodetect(self):
        """Test the `translators.Pet`'s `autodetect` parameter."""
        file = self.examples / "inputs/depnodep.c"
        cases = [
            (False, 1),
            (True, 3),
        ]
        for autodetect, num_scops in cases:
            with self.subTest(autodetect=autodetect):
                translator = Pet(autodetect=autodetect)
                translator.set_source(file)
                self.assertEqual(len(translator.scops), num_scops)

    @unittest.skip("todo")
    def test_pet_scop_extraction(self):
        """Test the things done in the constructor: does it populate
        ccscops and scops correctly."""

    @unittest.skip("todo")
    def test_pet_codegen(self):
        """Test codegen"""

    @unittest.skip("todo")
    def test_polly_codegen(self):
        """See same test for pet."""

    @unittest.skip("todo")
    def test_polly_scop_extraction(self):
        """See same test for pet."""
