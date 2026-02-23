#!/bin/env python

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--foo", action="append")
    args = parser.parse_args()
    print(args)
    print("scopdetection start")


if __name__ == "__main__":
    main()
