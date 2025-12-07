#!/bin/env python

import unittest
from pathlib import Path

from tadashi.translators import *


class TestTranslator(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    @unittest.skip("todo")
    def test_pet_scop_extraction(self):
        """Test the things done in the constructor: does it populate
        ccscops and scops correctly.

        !!! Consider other functionality. Also consider testing ccscop
            functionality.

        """

    @unittest.skip("todo")
    def test_pet_codegen(self):
        """Test codegen"""

    @unittest.skip("todo")
    def test_polly_codegen(self):
        """See same test for pet."""

    @unittest.skip("todo")
    def test_polly_scop_extraction(self):
        """See same test for pet."""
