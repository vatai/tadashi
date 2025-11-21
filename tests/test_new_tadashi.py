#!/bin/env python

import os
import unittest

import tadashi
from tadashi import translators


class TestNewTadashi(unittest.TestCase):
    def test_devel(self):
        filename = "foo.cpython-313-x86_64-linux-gnu.so"
        target = f"{__file__}/../../tadashi/{filename}"
        # a = foo.translators.Dummy()
        self.assertEqual(translators.mul(2, 3), 6)
        self.assertEqual(tadashi.add(2, 3), 5)
