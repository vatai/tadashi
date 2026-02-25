#!/bin/env python
import argparse
import re
from pathlib import Path

from tadashi.apps import Simple
from tadashi.translators import Pet, Polly


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the source files")
    parser.add_argument("extension", help="File extension 'c' or 'f'")
    parser.add_argument("-i", "--pet", action="store_true")
    parser.add_argument("-a", "--args", action="append")
    args = parser.parse_args()
    if not args.args:
        args.args = ["flang"]
    assert args.extension in "cf"
    return args


def print_app(app):
    pass


def main():
    args = get_args()
    patterns = {"f": r"\.f|f90", "c": r"\.c[^.]*$"}
    pattern = re.compile(patterns[args.extension], re.IGNORECASE)
    for file in Path(args.path).rglob("*"):
        if pattern.match(file.suffix):
            cls = Pet if args.pet else Polly
            translator = cls(*args.args)
            app = Simple(file, translator=translator)
            print_app(app)
    print("DONE")


if __name__ == "__main__":
    main()
