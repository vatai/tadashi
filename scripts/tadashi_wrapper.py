#!/usr/bin/env python

# Test/debug code to experintem with C-python interaction.
#
# Emil Vatai


import argparse
import sys
from pathlib import Path

import pexpect
import yaml

import process_yaml


def modify_schedule(schedule):
    print("== wrapper.py::modify_schedule begin ==")
    print(f"==orig==\n{schedule}")
    schedule = yaml.safe_load(schedule)
    process_yaml.dump_schedule_to_file(schedule)
    new_schedule = process_yaml.process_schedule(schedule)
    OptionsPool = process_yaml.OptionsPool(schedule)
    OptionsPoolRoot = OptionsPool.get_valid_range()
    # new_schedule.tile(4, [0])
    # new_schedule.tile(4, [0, 0, 0])
    # new_schedule.mark_parallel([0])
    new_schedule.interchange([0], [0, 0])
    # new_schedule.interchange([0, 0], [0, 0, 0])
    # new_schedule.tile(4, [0, 0, 0])
    # new_schedule.mark_parallel([0])
    # new_schedule.reverse([0])

    process_yaml.dump_schedule_to_file(new_schedule.yaml_schedule)
    print(f"== wrapper.py: ==\n{yaml.dump(new_schedule.yaml_schedule)=}")
    # with open('/barvinok/polyhedral-tutor/src/now_interchange_matmul.yaml', 'r') as file:
    #     new_schedule.yaml_schedule = yaml.safe_load(file)

    new_yaml = yaml.dump(
        new_schedule.yaml_schedule,
        sort_keys=False,
        default_flow_style=True,
        default_style='"',
        width=float("inf"),
    )
    pretty_new_yaml = yaml.dump(
        new_schedule.yaml_schedule,
        sort_keys=False,
        # default_flow_style=True,
        # default_style='"',
        width=float("inf"),
    )
    # print(f"==new==")
    print(f"== wrapper.py::pretty_new_yaml ==")
    print(pretty_new_yaml)
    print("== wrapper.py::modify_schedule end ==")
    return new_yaml


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
    child = pexpect.spawn(cmd, echo=False, maxread=1, encoding="utf-8", timeout=1)
    child.logfile = sys.stdout
    child.expect("WARNING: This app should only be invoked by the python wrapper!")
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
