#!/bin/env python
import argparse
import re
from pathlib import Path

import tadashi.translators
from tadashi import apps


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("files")
    parser.add_argument("extension")
    parser.add_argument("-i", "--pet", action="store_true")
    parser.add_argument("-a", "--args", action="append")
    return parser.parse_args()


def make_translator(args):
    if args.pet:
        translator = tadashi.translators.Pet(*args.translator_arg)
    else:
        polly_args = args.translator_arg
        if not polly_args:
            polly_args = ["flang"]
        print(f"{polly_args=}")
        translator = tadashi.translators.Polly(*polly_args)
    return translator


def main():
    args = get_args()
    print(args)
    files = [
        "foobar1.c",
        "foobar2.cc",
        "foobar3.cpp",
        "foobar4.c++",
        "foobar5.c.f",
        "foobar6.f90",
        "foobarU1.C",
        "foobarU2.cC",
        "foobarU3.CPp",
        "foobarU4.C++",
        "foobarU5.c.F",
        "foobarU6.F90",
    ]

    pat = r".*\.f|f90" if 1 else r".*\.c[^.]*$"
    pattern = re.compile(pat, re.IGNORECASE)
    for file in files:
        if pattern.match(file):
            print(file)
    print("DONE")


if __name__ == "__main__":
    main()
