#!/bin/env python


class BaseApp:
    def __init__(self, source, translator):
        self.source = source
        self.translator = translator(source)

    @property
    def scops(self):
        return self.translator.scops
