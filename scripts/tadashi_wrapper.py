#!/usr/bin/env python

# Test/debug code to experintem with C-python interaction.
#
# Emil Vatai


import argparse
import sys
from pathlib import Path

import pexpect
import yaml


def modify_schedule(schedule):
    print(f"==orig==\n{schedule}")
    new_schedule = schedule.replace("[(i)]", "[(i)]")
    new_schedule = yaml.safe_load(new_schedule)
    print(f"==dict==\n{new_schedule}")
    new_schedule = yaml.dump(
        new_schedule,
        sort_keys=False,
        default_flow_style=True,
        default_style='"',
        width=float("inf"),
    )
    print(f"==new==\n{new_schedule}")
    return new_schedule


# def construct_tadashi_command(args):
#     return args


def invoke_tadashi(input_file_path, output_file_path, tadashi_args):
    tadashi_bin = Path(__file__).parent.parent / "build/tadashi"
    cmd = [tadashi_bin, input_file_path, *tadashi_args]
    if output_file_path:
        cmd += ["-o", output_file_path]
    cmd = " ".join(map(str, cmd))
    print(f"Calling: {cmd}")
    patterns = [
        "### sched\[.*\] begin ###.*### sched\[.*\] end ###\r\n",
        "### STOP ###\r\n",
    ]
    child = pexpect.spawn(cmd, echo=False, maxread=1, encoding="utf-8")  # , timeout=1)
    # child.logfile = sys.stdout
    child.expect("WARNING: This app should only be invoced by the python wrapper!")
    while 0 == child.expect(patterns):
        schedule = child.after.rstrip()
        new_schedule = modify_schedule(schedule)
        child.sendline(new_schedule)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_path", type=Path)
    parser.add_argument("-o", dest="output_file_path", type=Path)
    args, tadashi_args = parser.parse_known_args()
    invoke_tadashi(
        input_file_path=args.input_file_path,
        output_file_path=args.output_file_path,
        tadashi_args=tadashi_args,
    )
    print("DONE")
