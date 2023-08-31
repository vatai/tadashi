#!/usr/bin/env python

# Test/debug code to experintem with C-python interaction.
#
# Emil Vatai


import pexpect
import yaml


def modify_schedule(schedule):
    return schedule.replace("[(i)]", "[(-i)]")


def main():
    cmd = "./build/tadashi ./examples/depnodep.c"
    # cmd = "./build/c_python_interact"
    patterns = [
        "### sched\[.*\] begin ###.*### sched\[.*\] end ###\r\n",
        "### STOP ###\r\n",
    ]
    child = pexpect.spawn(cmd, echo=False, maxread=1, timeout=1)

    match = child.expect(patterns)
    while 0 == match:
        sched0 = child.after.decode().rstrip()
        print(f"{yaml.safe_load(sched0)=}")
        assert child.before.rstrip() == b"", f"{child.before=}"

        new_schedule = modify_schedule(sched0)
        child.sendline(new_schedule)
        child.sendeof()

        match = child.expect(patterns)


if __name__ == "__main__":
    main()
    print("DONE")
