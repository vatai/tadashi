#!/bin/env python

import unittest

from tadashi import apps, translators


class TestNewTadashi(unittest.TestCase):
    def test_devel(self):
        app = apps.Simple("examples/inputs/depnodep.c", translators.Pet())
        self.assertEqual(len(app.scops), 1)
        s = str(app.scops[0])
        self.assertEqual(
            s,
            """{ domain: "[N] -> { S_0[j, i] : 0 < j < N and 0 < i < N }", child: { schedule: "[N] -> L_0[{ S_0[j, i] -> [(j)] }]", child: { schedule: "[N] -> L_1[{ S_0[j, i] -> [(i)] }]" } } }""",
        )

    @unittest.skip("debugging")
    def test_tranfo(self):
        app = apps.Simple("examples/inputs/depnodep.c", translators.Pet())
        s = app.scops[0]
        s.foobar_transform(1)
