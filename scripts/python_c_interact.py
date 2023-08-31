#!/usr/bin/env python

# Test/debug code to experintem with C-python interaction.
#
# Emil Vatai


import pexpect
import yaml


def get_schedule(child):
    lines = child.after.decode().split("\r\n")
    return lines[1].rstrip()


def modify_schedule(schedule):
    return schedule.replace("[(i)]", "[(-i)]")


def main():
    patterns = ["### sched\[.*\] begin ###.*### sched\[.*\] end ###", "### STOP ###"]
    cmd = "./build/c_python_interact"
    child = pexpect.spawn(cmd, echo=False, maxread=1)

    match = child.expect(patterns)
    while 0 == match:
        print(f"{match} <<<<<<")
        sched0 = get_schedule(child)
        print(f"{yaml.safe_load(sched0)=}")
        assert child.before.rstrip() == b"", child.before

        new_schedule = modify_schedule(sched0)
        child.sendline(new_schedule)

        match = child.expect(patterns)
        assert match == 0
        print(f"{match} --")
        sched1 = get_schedule(child)
        print(f"{yaml.safe_load(sched1)=}")
        assert child.before.rstrip() == b"", child.before
        print("======")
        match = child.expect(patterns)
        print(f"{match} >>>>>>>")


if __name__ == "__main__":
    main()
