#!/bin/env python
import argparse
import re
from pathlib import Path

from tadashi.apps import Simple
from tadashi.translators import Pet, Polly


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the source files")
    parser.add_argument(
        "-e", "--extension", help="File extension 'c' or 'f'", default="f"
    )
    parser.add_argument("-i", "--pet", action="store_true")
    parser.add_argument("-a", "--args", action="append")
    args = parser.parse_args()
    if not args.args:
        args.args = ["flang"]
    assert args.extension in "cf"
    return args


def print_app(app):
    for scop_idx, scop in enumerate(app.scops):
        num_nodes = len(scop.schedule_tree)
        node_depts = [len(n.location) for n in scop.schedule_tree]
        max_depth = max(node_depts)
        print(f"scop: {scop_idx} - {num_nodes=} - {max_depth=}")


def scop_detector():
    args = get_args()
    patterns = {"f": r"\.f|f90", "c": r"\.c[^.]*$"}
    pattern = re.compile(patterns[args.extension], re.IGNORECASE)
    for file in Path(args.path).rglob("*"):
        if pattern.match(file.suffix):
            cls = Pet if args.pet else Polly
            translator = cls(*args.args)
            app = Simple(file, translator=translator)
            print_app(app)
    print("DONE detecting")


def scop_printer():
    args = get_args()
    patterns = {"f": r"\.f|f90", "c": r"\.c[^.]*$"}
    pattern = re.compile(patterns[args.extension], re.IGNORECASE)
    path = Path(args.path)
    cls = Pet if args.pet else Polly
    translator = cls(*args.args)
    app = Simple(str(path), translator=translator)
    for idx, scop in enumerate(app.scops):
        print(f"SCOP[{idx}]")
        print(scop.schedule_tree[0].yaml_str)
    print("DONE printing")


if __name__ == "__main__":
    pass
