#!/usr/bin/env python

# Test/debug code to experintem with C-python interaction.
#
# Emil Vatai


import pexpect

cmd = ["./build/c_python_interact"]
SCHED = '{ domain: "[N, i] -> { S_0[] }" }'

child = pexpect.spawn(cmd[0])
child.expect(".*domain.*")
sched0 = child.after.rstrip().decode().split("\r\n")[-1]
print(f"{sched0=}")

child.sendline(sched0.replace("[(i)]", "[(-i)]"))

child.expect("{ domain.*$")
sched1 = child.after.rstrip().decode().split("\r\n")[-1]
print(f"{sched1=}")

child.expect("{ domain.*$")
sched3 = child.after.rstrip().decode().split("\r\n")[-1]
print(f"{sched3=}")
child.sendline(SCHED)

child.expect("{ domain.*$")
sched4 = child.after.rstrip().decode().split("\r\n")[-1]
print(f"{sched4=}")
