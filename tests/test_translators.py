#!/bin/env python

import pickle
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

    # TODO
    def _test_scop_extraction(self, translator: Translator):
        """Test the things done in the constructor: does it populate
        ccscops and scops correctly."""
        translator.set_source(self.examples / "inputs/depnodep.c", [])
        for s in translator.scops:
            for n in s.schedule_tree:
                self.assertTrue(str(n))

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

    @staticmethod
    def _scop_yamls(translator: Translator) -> list[str]:
        """Snapshot every scop's schedule via the root node's yaml_str."""
        return [s.schedule_tree[0].yaml_str for s in translator.scops]

    @staticmethod
    def _first_tilable(scop):
        """Find the first node that accepts a 1D tile."""
        for node in scop.schedule_tree:
            if TrEnum.TILE_1D in node.available_transformations:
                return node
        return None

    def _test_pickle_roundtrip(self, translator: Translator):
        """Pickle/unpickle reproduces the same scops."""
        file = self.examples / "inputs/depnodep.c"
        translator.set_source(file, [])
        original_yamls = self._scop_yamls(translator)

        restored = pickle.loads(pickle.dumps(translator))

        self.assertEqual(len(translator.scops), len(restored.scops))
        self.assertEqual(original_yamls, self._scop_yamls(restored))

    def _test_pickle_after_modify(self, translator: Translator):
        """Modifying scops must not break pickling.

        The unpickled translator is expected to have *fresh* scops
        (modifications are not preserved by design — `__setstate__`
        re-runs `set_source`/`populate_ccscops`).

        """
        file = self.examples / "inputs/depnodep.c"
        translator.set_source(file, [])
        pristine_yamls = self._scop_yamls(translator)

        node = self._first_tilable(translator.scops[0])
        self.assertIsNotNone(node, "Need a tilable band node for this test")
        node.transform(TrEnum.TILE_1D, 32)

        modified_yamls = self._scop_yamls(translator)
        self.assertNotEqual(
            pristine_yamls,
            modified_yamls,
            "Sanity: TILE_1D should change the schedule tree",
        )

        restored = pickle.loads(pickle.dumps(translator))

        self.assertEqual(
            modified_yamls,
            self._scop_yamls(restored),
            "Unpickled translator should have modified scops",
        )

    def _test_pickle_preserves_state_after_modify(self, translator: Translator):
        """Modifying scops must not corrupt the translator's pickled
        state: a pickle taken after a transform still restores to the
        un-modified scops (same as a pickle taken before the transform).

        """
        self.assertTrue(False)
        file = self.examples / "inputs/depnodep.c"
        translator.set_source(file, [])
        pristine_yamls = self._scop_yamls(translator)

        # Pickle BEFORE modifying.
        pickle_before = pickle.dumps(translator)

        node = self._first_tilable(translator.scops[0])
        self.assertIsNotNone(node)
        node.transform(TrEnum.TILE_1D, 32)

        # Pickle AFTER modifying.
        pickle_after = pickle.dumps(translator)

        restored_before = pickle.loads(pickle_before)
        restored_after = pickle.loads(pickle_after)

        self.assertEqual(pristine_yamls, self._scop_yamls(restored_before))
        self.assertEqual(pristine_yamls, self._scop_yamls(restored_after))


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

    def test_pickle_roundtrip(self):
        self._test_pickle_roundtrip(Pet())

    def test_pickle_roundtrip_autodetect(self):
        """The autodetect flag must survive pickling.

        depnodep.c yields 1 scop without autodetect and 3 with it; the
        unpickled Pet must agree with the original on this count.

        """
        file = self.examples / "inputs/depnodep.c"
        translator = Pet(autodetect=True)
        translator.set_source(file, [])
        restored = pickle.loads(pickle.dumps(translator))
        self.assertEqual(len(restored.scops), 3)

    def test_pickle_after_modify(self):
        self._test_pickle_after_modify(Pet())

    def test_pickle_preserves_state_after_modify(self):
        self._test_pickle_preserves_state_after_modify(Pet())


class TestPolly(TestTranslator):
    def test_compilation_error(self):
        self._test_compilation_error(Polly("clang"))

    def test_wip(self):
        translator = Polly("clang")
        input_path = self.examples / "inputs/depnodep.c"
        translator.set_source(input_path, [])
        scop = translator.scops[0]
        node = scop.schedule_tree[1]
        # print(node.yaml_str)
        # node.transform(TrEnum.INTERCHANGE)
        # print(node.yaml_str)
        translator.generate_code(str(input_path), "/tmp/output.ll", [])

    def test_pickle_roundtrip(self):
        self._test_pickle_roundtrip(Polly("clang"))

    def test_pickle_after_modify(self):
        self._test_pickle_after_modify(Polly("clang"))

    def test_pickle_preserves_state_after_modify(self):
        self._test_pickle_preserves_state_after_modify(Polly("clang"))
