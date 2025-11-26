#!/bin/env python

import os
import unittest

import tadashi
from tadashi import apps, translators


class TestNewTadashi(unittest.TestCase):
    def test_devel(self):
        app = apps.BaseApp("examples/inputs/depnodep.c", translators.Pet)
        # print(f"{app.scops=}")
        print("OK!")
        for s in app.translator.scops:
            print(f"{s}")
