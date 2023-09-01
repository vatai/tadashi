#!/usr/bin/env python

# Test/debug code to experintem with C-python interaction.
#
# Emil Vatai


import sys

import pexpect
import yaml


def modify_schedule(schedule):
    return schedule.replace("[(i)]", "[(-i)]")


def invoke_tadashi(input_file):
    cmd = f"./build/tadashi {input_file}"
    print(f"Calling: {cmd}")
    patterns = [
        "### sched\[.*\] begin ###.*### sched\[.*\] end ###\r\n",
        "### STOP ###\r\n",
    ]
    child = pexpect.spawn(cmd, echo=False, maxread=1)  # , timeout=1)
    child.expect("WARNING: This app should only be invoced by the python wrapper!")
    while 0 == child.expect(patterns):
        print(child.before.decode())
        sched0 = child.after.decode().rstrip()
        print(f"{yaml.safe_load(sched0)=}")
        # assert child.before.rstrip() == b"", f"{child.before=}"

        new_schedule = modify_schedule(sched0)
        child.sendline(new_schedule)
        child.sendeof()


if __name__ == "__main__":
    invoke_tadashi(input_file=sys.argv[1])
    print("DONE")
