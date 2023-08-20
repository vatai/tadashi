#!/usr/bin/env python

# Test/debug code to experintem with C-python interaction.
#
# Emil Vatai


import pexpect

cmd = ["./build/c_python_interact"]
SCHED = '{ domain: "[N, i] -> { S_0[] }" }'
pattern = "### sched\[.*\] begin ###.*### sched\[.*\] end ###"


def get_schedule(child):
    print(f">>> {child.before=}")
    print(f">>> {child.after=}")
    return child.after.rstrip().decode().split("\r\n")[1]


child = pexpect.spawn(cmd[0], echo=False)

child.expect(pattern)
sched0 = get_schedule(child)
print(f"{sched0=}")
assert child.before.rstrip() == b"", child.before

child.sendline(sched0.replace("[(i)]", "[(-i)]"))

child.expect(pattern)
sched1 = get_schedule(child)
print(f"{sched1=}")
assert child.before.rstrip() == b"", child.before

child.expect(pattern)
sched2 = get_schedule(child)
print(f"{sched2=}")
assert child.before.rstrip() == b"", child.before

child.sendline(SCHED)

child.expect(pattern)
sched4 = get_schedule(child)
print(f"{sched4=}")
assert child.before.rstrip() == b"", child.before
