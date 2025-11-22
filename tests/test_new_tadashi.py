#!/bin/env python

import os
import unittest

import tadashi
from tadashi import apps, translators


class TestNewTadashi(unittest.TestCase):
    def test_devel(self):
        app = apps.BaseApp("source", translators.Pet)
        print(f"{len(app.scops)=}")
        for scop in app.scops:
            print(scop)
        self.assertEqual(translators.mul(2, 3), 6)
        self.assertEqual(tadashi.add(2, 3), 5)
