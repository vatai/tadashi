#!/bin/env python

import tempfile
import unittest
from pathlib import Path

from tadashi.scop import Scop, TrEnum
from tadashi.translators import *


class TestTranslator(unittest.TestCase):
    """!!! Consider other functionality. Also consider testing ccscop
    functionality.

    """

    examples: Path = Path(__file__).parent.parent / "examples"
    tests: Path = Path(__file__).parent

    def _test_scop_extraction(self, translator: Translator):
        """Test the things done in the constructor: does it populate
        ccscops and scops correctly."""
        translator.set_source(self.examples / "inputs/depnodep.c", [])
        for s in translator.scops:
            for n in s.schedule_tree:
                print(n)

    @unittest.skip("todo")
    def _test_codegen(self):
        """Test codegen"""

    def _test_double_set(self, translator):
        """Calling set_source() 2x on a translator should raise an error!"""
        file = self.examples / "inputs/depnodep.c"
        translator.set_source(file, [])
        with self.assertRaises(RuntimeError):
            translator.set_source(file, [])

    def _test_deleted_translator(self, translator_cls):
        """This test should simply not crash."""

        def _get_schedule_tree():
            file = self.examples / "inputs/depnodep.c"
            translator = translator_cls()
            translator.set_source(file, [])
            scop = translator.scops[0]
            # `translator` is freed after the next line.
            return scop.schedule_tree

        with self.assertRaises(RuntimeError):
            node = _get_schedule_tree()[1]
            # The translator is qeried when in the next line!
            print(node.yaml_str)

    def _test_compilation_error(self, translator):
        with self.assertRaises(ValueError):
            path = self.tests / "syntax_error.c"
            self.assertTrue(path.exists())
            translator.set_source(path, [])


class TestPet(TestTranslator):
    def test_non_existing_file(self):
        """Test if Pet errors out when we try to open an non-existing file."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "does-not-exists.c"
            self.assertFalse(path.exists())
            with self.assertRaises(ValueError):
                translator = Pet()
                translator.set_source(path, [])

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

    def test_scop_extraction(self):
        """Test the things done in the constructor: does it populate
        ccscops and scops correctly."""
        self._test_scop_extraction(Pet())

    def test_double_set(self):
        self._test_double_set(Pet())

    def test_deleted_translator(self):
        self._test_deleted_translator(Pet)

    def test_compilation_error(self):
        self._test_compilation_error(Pet(autodetect=True))


class TestPolly(TestTranslator):
    def test_compilation_error(self):
        self._test_compilation_error(Polly("clang"))

    def test_wip(self):
        translator = Polly("clang")
        print("Setting sources... ", end="")
        input_path = self.examples / "inputs/depnodep.c"
        translator.set_source(input_path, [])
        print("DONE!")
        scop = translator.scops[1]
        node = scop.schedule_tree[2]
        print(node.yaml_str)
        node.transform(TrEnum.INTERCHANGE)
        scop = translator.scops[1]
        node = scop.schedule_tree[2]
        print(node.yaml_str)
        translator.generate_code(str(input_path), "/tmp/output.ll", [])
