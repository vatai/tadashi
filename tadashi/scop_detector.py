#!/bin/env python

import argparse
from pathlib import Path

import tadashi.translators
from tadashi import apps


def get_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-i", "--pet", action="store_true")
    group.add_argument("-l", "--polly", action="store_true", default=True)
    parser.add_argument(
        "-a",
        "--translator_arg",
        action="append",
    )
    parser.add_argument("files")
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


if __name__ == "__main__":
    main()
