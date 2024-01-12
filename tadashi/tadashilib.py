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

get_num_scops = _tadashi.get_num_scops
get_num_scops.argtypes = [c_char_p]

goto_parent = _tadashi.goto_parent

goto_child = _tadashi.goto_child
goto_child.argtypes = [c_long, c_long]

get_num_children = _tadashi.get_num_children
get_num_children.argtypes = [c_long]

get_dim_names = _tadashi.get_dim_names
get_dim_names.restype = c_char_p
get_dim_names.argtypes = [c_long]

get_type = _tadashi.get_type
get_type.restype = c_int
get_type.argtypes = [c_long]

get_type_str = _tadashi.get_type_str
get_type_str.restype = c_char_p
get_type_str.argtypes = [c_long]

get_expr = _tadashi.get_expr
get_expr.restype = c_char_p
get_expr.argtypes = [c_long]

free_scops = _tadashi.free_scops

scan_source(b"./examples/depnodep.c")
num_scopes = get_num_scops(b"./examples/depnodep.c")
print(f"{num_scopes=}")
# child(0, 0)

print(f"{get_num_children(0)=}")

print(f"{get_dim_names(0)=}")


def traverse(scop_idx, nodes, parent):
    num_children = get_num_children(scop_idx)
    inner_dim_names = get_dim_names(scop_idx).decode().split(";")[:-1]
    dim_names = [t.split("|")[:-1] for t in inner_dim_names]
    node = dict(
        type=get_type(scop_idx),
        type_str=get_type_str(scop_idx),
        num_children=num_children,
        children=[-1 for _ in range(num_children)],
        parent=parent,
        dim_names=dim_names,
        expr=get_expr(scop_idx),
    )
    print(f"{node=}")
    parent_idx = len(nodes)
    nodes.append(node)
    if node["type"] == 6:  # 6 = LEAF
        return
    else:
        for c in range(num_children):
            goto_child(scop_idx, c)
            node["children"][c] = len(nodes)
            traverse(scop_idx, nodes, parent_idx)
            goto_parent(scop_idx)


def get_schedule_tree(scop_idx):
    nodes = []
    traverse(scop_idx, nodes, parent=-1)
    print(nodes)
    return nodes


schedules_trees = []
for i in range(num_scopes):
    sch_tree = get_schedule_tree(i)
    schedules_trees.append(sch_tree)


free_scops()

print("PYTHON DONE")
