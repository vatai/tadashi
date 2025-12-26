#!/usr/bin/env python

"""Main Tadashi package."""


rtd = os.environ.get("READTHEDOCS")

if rtd != "True":
    from ctadashi import ctadashi
