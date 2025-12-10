#!/bin/env python

import unittest
from pathlib import Path
from typing import Callable

from tadashi.apps import Simple
from tadashi.node_type import NodeType
from tadashi.translators import Pet


class TestScop(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def _get_schedule_tree(self):
        file = self.examples / "inputs/depnodep.c"
        translator = Pet()
        translator.set_source(file)
        scop = translator.scops[0]
        return scop.schedule_tree

    def test_schedule_tree(self):
        """Test the basic schedule_tree functionality."""
        self.assertEqual(len(self._get_schedule_tree()), 4)


class TestNode(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def _get_schedule_tree(self):
        file = self.examples / "inputs/depnodep.c"
        translator = Pet()
        translator.set_source(file)
        scop = translator.scops[0]
        return scop.schedule_tree

    def _assert_perperties_equal(self, target: list, fn: Callable):
        for idx, node in enumerate(self._get_schedule_tree()):
            with self.subTest(idx=idx):
                self.assertEqual(fn(node), target[idx])

    def test_node_type(self):
        target = [NodeType.DOMAIN, NodeType.BAND, NodeType.BAND, NodeType.LEAF]
        self._assert_perperties_equal(target, lambda t: t.node_type)

    def test_num_children(self):
        target = [1, 1, 1, 0]
        self._assert_perperties_equal(target, lambda t: t.num_children)

    def test_parent_idx(self):
        target = [-1, 0, 1, 2]
        self._assert_perperties_equal(target, lambda t: t.parent_idx)

    def test_index(self):
        target = [0, 1, 2, 3]
        self._assert_perperties_equal(target, lambda t: t.index)

    def test_label(self):
        target = ["", "L_0", "L_1", ""]
        self._assert_perperties_equal(target, lambda t: t.label)

    def test_location(self):
        target = [[], [0], [0, 0], [0, 0, 0]]
        self._assert_perperties_equal(target, lambda t: t.location)

    def test_loop_signature(self):
        target = [
            "[]",
            "[{'params': ['N'], 'vars': ['j', 'i']}]",
            "[{'params': ['N'], 'vars': ['j', 'i']}]",
            "[]",
        ]
        self._assert_perperties_equal(target, lambda t: t.loop_signature)

    def test_expr(self):
        target = [
            "",
            "[N] -> L_0[{ S_0[j, i] -> [(j)] }]",
            "[N] -> L_1[{ S_0[j, i] -> [(i)] }]",
            "",
        ]
        self._assert_perperties_equal(target, lambda t: t.expr)

    def test_children_idx(self):
        target = [[1], [2], [3], []]
        self._assert_perperties_equal(target, lambda t: t.children_idx)

    def test_yaml_str(self):
        app = Simple(self.examples / "inputs/depnodep.c", Pet())
        yamls = [
            """# YOU ARE HERE
domain: "[N] -> { S_0[j, i] : 0 < j < N and 0 < i < N }"
child:
  schedule: "[N] -> L_0[{ S_0[j, i] -> [(j)] }]"
  child:
    schedule: "[N] -> L_1[{ S_0[j, i] -> [(i)] }]"
""",
            """domain: "[N] -> { S_0[j, i] : 0 < j < N and 0 < i < N }"
child:
  # YOU ARE HERE
  schedule: "[N] -> L_0[{ S_0[j, i] -> [(j)] }]"
  child:
    schedule: "[N] -> L_1[{ S_0[j, i] -> [(i)] }]"
""",
            """domain: "[N] -> { S_0[j, i] : 0 < j < N and 0 < i < N }"
child:
  schedule: "[N] -> L_0[{ S_0[j, i] -> [(j)] }]"
  child:
    # YOU ARE HERE
    schedule: "[N] -> L_1[{ S_0[j, i] -> [(i)] }]"
""",
            """domain: "[N] -> { S_0[j, i] : 0 < j < N and 0 < i < N }"
child:
  schedule: "[N] -> L_0[{ S_0[j, i] -> [(j)] }]"
  child:
    schedule: "[N] -> L_1[{ S_0[j, i] -> [(i)] }]"
    child:
      # YOU ARE HERE
      leaf
""",
        ]
        nodes = app.scops[0].schedule_tree
        for idx, node in enumerate(nodes):
            self.assertEqual(node.yaml_str, yamls[idx])
