#!/bin/env python
import argparse
import os
import re
from pathlib import Path

from tadashi.apps import Simple
from tadashi.translators import Pet, Polly


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to the source file/dir")
    parser.add_argument(
        "-e",
        "--extension",
        help="File extension 'c' or 'f'",
        default="c",
    )
    parser.add_argument(
        "-i",
        "--pet",
        action="store_true",
        help="Use PET instead of polly",
    )
    parser.add_argument(
        "-a",
        "--args",
        default=[],
        action="append",
        help="Args passed to the Polly/PET translator (can be used multiple times)",
    )
    args, rest = parser.parse_known_args()
    args.rest = rest
    assert args.extension in "cf"
    return args


def _print_summary(app):
    print(f"{len(app.scops)=}")
    for scop_idx, scop in enumerate(app.scops):
        num_nodes = len(scop.schedule_tree)
        node_depts = [len(n.location) for n in scop.schedule_tree]
        max_depth = max(node_depts)
        print(f"scop: {scop_idx} - {num_nodes=} - {max_depth=}")


def _mkapp(args, file):
    cls = Pet if args.pet else Polly
    print(f"{cls.__name__}({", ".join(args.args)}) for {str(file)}")
    translator = cls(*args.args)
    app = Simple(file, translator=translator, compiler_options=args.rest)
    return app


def scop_detector():
    args = _get_args()
    patterns = {"f": r"\.f|f90", "c": r"\.c[^.]*$"}
    pattern = re.compile(patterns[args.extension], re.IGNORECASE)
    for fidx, file in enumerate(Path(args.path).glob("*")):
        if pattern.match(file.suffix):
            app = _mkapp(args, file)
            _print_summary(app)
    print(f"{fidx+1} files parsed")
    print("DONE detecting")


def scop_printer():
    args = _get_args()
    file = Path(args.path)
    app = _mkapp(args, file)
    for idx, scop in enumerate(app.scops):
        print(f"SCOP[{idx}]")
        print(scop.schedule_tree[0].yaml_str)
    print("DONE printing")


if __name__ == "__main__":
    pass
