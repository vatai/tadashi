#!/bin/env python

import tempfile
import unittest
from pathlib import Path

from tadashi.scop import Scop
from tadashi.translators import *


class TestTranslator(unittest.TestCase):
    """!!! Consider other functionality. Also consider testing ccscop
    functionality.

    """

    examples: Path = Path(__file__).parent.parent / "examples"
    tests: Path = Path(__file__).parent

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
                translator.set_source(file, [])
                self.assertEqual(len(translator.scops), num_scops)

    def test_double_set(self):
        """Calling set_source() 2x on a translator should raise an error!"""
        translator = Pet()
        file = self.examples / "inputs/depnodep.c"
        translator.set_source(file, [])
        with self.assertRaises(RuntimeError):
            translator.set_source(file, [])

    def test_deleted_translator(self):
        """This test should simply not crash."""

        def _get_schedule_tree():
            file = self.examples / "inputs/depnodep.c"
            translator = Pet()
            translator.set_source(file, [])
            scop = translator.scops[0]
            # `translator` is freed after the next line.
            return scop.schedule_tree

        with self.assertRaises(RuntimeError):
            node = _get_schedule_tree()[1]
            # The translator is qeried when in the next line!
            print(node.yaml_str)

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


class TestPet(TestTranslator):
    def test_non_existing_file(self):
        """Test if Pet errors out when we try to open an non-existing file."""
        with tempfile.TemporaryDirectory() as tmp:
            print(f"{tmp=} {type(tmp)=}")
            path = Path(tmp) / "does-not-exists.c"
            self.assertFalse(path.exists())
            with self.assertRaises(ValueError):
                translator = Pet()
                translator.set_source(path, [])

    def test_compilation_error(self):
        with self.assertRaises(ValueError):
            translator = Pet(autodetect=True)
            path = self.tests / "syntax_error.c"
            self.assertTrue(path.exists())
            translator.set_source(path, [])
