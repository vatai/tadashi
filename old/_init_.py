#!/usr/bin/env python

"""Main Tadashi package."""


rtd = os.environ.get("READTHEDOCS")

if rtd != "True":
    from ctadashi import ctadashi


class Scops:
    @staticmethod
    def _check_missing_file(path: Path):
        if not path.exists():
            raise ValueError(f"{path} does not exist!")
