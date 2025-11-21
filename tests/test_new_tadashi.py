#!/bin/env python

import os
import unittest

import tadashi
from tadashi import translators


class TestNewTadashi(unittest.TestCase):
    def test_devel(self):
        target = os.path.abspath(f"{__file__}/../../tadashi/translators.py")
        self.assertEqual(translators.__file__, target)
