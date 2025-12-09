#!/bin/env python

import unittest
from pathlib import Path
from typing import Callable

from tadashi import TrEnum
from tadashi.node_type import NodeType
from tadashi.translators import Pet


class TestNode(unittest.TestCase):
    examples: Path = Path(__file__).parent.parent / "examples"

    def _get_schedule_tree(self):
        file = self.examples / "inputs/depnodep.c"
        translator = Pet()
        translator.set_source(file)
        self.scop = translator.scops[0]
        return self.scop.schedule_tree

    def test_interchange(self):
        """Test the basic schedule_tree functionality."""
        node = self._get_schedule_tree()[1]
        node.transform(TrEnum.TILE2D, 4, 6)

    def test_tile2d(self):
        """Test the basic schedule_tree functionality."""
        node = self._get_schedule_tree()[2]
