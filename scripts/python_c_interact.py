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
    pattern = "### sched\[.*\] begin ###.*### sched\[.*\] end ###"
    cmd = "./build/c_python_interact"
    child = pexpect.spawn(cmd, echo=False)

    child.expect(pattern)
    sched0 = get_schedule(child)
    print(f"{yaml.safe_load(sched0)=}")
    assert child.before.rstrip() == b"", child.before

    child.sendline(modify_schedule(sched0))

    child.expect(pattern)
    sched1 = get_schedule(child)
    print(f"{sched1=}")
    assert child.before.rstrip() == b"", child.before

    child.expect(pattern)
    sched2 = get_schedule(child)
    print(f"{sched2=}")
    assert child.before.rstrip() == b"", child.before

    child.sendline(modify_schedule(sched2))

    child.expect(pattern)
    sched3 = get_schedule(child)
    print(f"{sched3=}")
    assert child.before.rstrip() == b"", child.before


if __name__ == "__main__":
    main()
