#!/bin/env python

from .translators import Translator


class BaseApp:
    def __init__(self, source: str, translator: Translator):
        self.source = source
        self.translator = translator.set_source(source)

    @property
    def scops(self):
        return self.translator.scops
