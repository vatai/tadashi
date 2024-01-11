#!/usr/bin/env python

from ctypes import (CDLL, POINTER, Structure, c_char_p, c_int, c_long,
                    c_longlong, c_size_t)
from pathlib import Path

########################################


class cell_t(Structure):
    pass


cell_t._fields_ = [("name", c_longlong), ("next", POINTER(cell_t))]

so_path = Path(__file__).parent.parent / "build/libctadashi.so"
print(so_path)
_tadashi = CDLL(so_path)

_tadashi.foo.restype = POINTER(cell_t)
_tadashi.foo.argtypes = [c_size_t]
foo = _tadashi.foo

_tadashi.bar.restype = c_size_t
_tadashi.bar.argtypes = [POINTER(cell_t)]
bar = _tadashi.bar

c = foo(10)
# print(c)
print(bar(c))

########################################

scan_source = _tadashi.scan_source
scan_source.argtypes = [c_char_p]
scan_source(b"./examples/depnodep.c")

get_num_scops = _tadashi.get_num_scops
get_num_scops.argtypes = [c_char_p]
num_scopes = get_num_scops(b"./examples/depnodep.c")
print(f"{num_scopes=}")

child = _tadashi.child
child.argtypes = [c_long, c_long]
child(0, 0)

num_children = _tadashi.num_children
num_children.argtypes = [c_long, c_long]
num_children(0)

dim_names = _tadashi.dim_names
dim_names.restype = c_char_p
dim_names.argtypes = [c_long]
print(dim_names(0))

get_type = _tadashi.get_types
dim_names.restype = c_int
dim_names.argtypes = [c_long]


def traverse(i, r):
    t = get_type(i)
    if t == LEAF:
        result = (t, 0)
        r.append(result)
        return
    else:
        n_chld = num_children(i)
        result = (t, n_chld)
        r.append(result)
        for c in range(num_children)


def get_schedule_tree(i):
    result = []
    traverse(i, result)
    return result


schedules_trees = []
for i in range(num_scopes):
    sch_tree = get_schedule_tree(i)
    schedules_trees.append(sch_tree)


free_scops = _tadashi.free_scops
free_scops()

print("PYTHON DONE")
