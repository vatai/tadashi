#!/usr/bin/env python3
import re
import sys

C_FILE = "tadashi/src/transformations.c"
H_FILE = "tadashi/src/transformations.h"
PXD_FILE = "tadashi/transformations.pxd"
PY_FILE = "tadashi/_tr_wrappers.py"

HEADER_H = """/** @file */
#ifndef TRANSFORMATIONS_H
#define TRANSFORMATIONS_H

#include <isl/schedule.h>
#include <isl/schedule_node.h>

#if defined(__cplusplus)
extern "C" {
#endif

"""

FOOTER_H = """
#if defined(__cplusplus)
}
#endif

#endif // TRANSFORMATIONS_H
"""

HEADER_PXD = """# -*- mode:cython -*-

from tadashi.isl cimport *

cdef extern from "transformations.h":
"""

HEADER_PY = """#!/bin/env python

import cython
from cython.cimports.tadashi import isl
from cython.cimports.tadashi.scop import Scop
from cython.cimports.tadashi.transformations import *

"""

# Regex to find tadashi transformations
# Look for: __isl_give isl_schedule_node * tadashi_name(...) {
# This is a bit brittle but should work for the coding style used.
REGEX = re.compile(
    r"^(__isl_give\s+)?isl_schedule_node\s*\*\s*\n?" r"(tadashi_\w+)\(([^)]+)\)\s*\{",
    re.MULTILINE | re.DOTALL,
)


def parse_args(args_str):
    """Parse C arguments into a list of (type, name)."""
    # Remove newlines and extra spaces
    args_str = " ".join(args_str.split())
    args_list = []

    # Split by comma
    parts = args_str.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Simple heuristic: last word is name, rest is type
        # Handle pointers and annotations
        part = (
            part.replace("__isl_take ", "")
            .replace("__isl_keep ", "")
            .replace("__isl_give ", "")
        )

        # Check for pointer *
        if "*" in part:
            type_part, name_part = part.rsplit("*", 1)
            type_part += "*"
            name_part = name_part.strip()
            if not name_part:  # e.g. "int *"
                continue
        else:
            # splitting "int size"
            subparts = part.rsplit(" ", 1)
            if len(subparts) == 2:
                type_part, name_part = subparts
            else:
                # Fallback or weird case
                type_part = part
                name_part = "arg"

        args_list.append((type_part.strip(), name_part.strip()))
    return args_list


def generate():
    with open(C_FILE, "r") as f:
        content = f.read()

    funcs = []
    for match in REGEX.finditer(content):
        func_name = match.group(2)
        args_str = match.group(3)
        args = parse_args(args_str)
        funcs.append((func_name, args))

    # Generate .h
    with open(H_FILE, "w") as f:
        f.write(HEADER_H)
        for name, args in funcs:
            arg_str = ", ".join([f"{t} {n}" for t, n in args])
            f.write(f"isl_schedule_node *{name}({arg_str});\n")
        f.write(FOOTER_H)

    # Generate .pxd
    with open(PXD_FILE, "w") as f:
        f.write(HEADER_PXD)
        for name, args in funcs:
            arg_str = ", ".join([f"{t} {n}" for t, n in args])
            f.write(f"    cdef isl_schedule_node *{name}({arg_str})\n")

    # Generate .py
    with open(PY_FILE, "w") as f:
        f.write(HEADER_PY)
        for name, args in funcs:
            py_name = name.replace("tadashi_", "")

            # Build python signature and C call args
            py_args = []
            c_args = []

            # First arg is always node/scop
            # Check if first arg is isl_schedule_node*
            if args and "isl_schedule_node" in args[0][0]:
                py_args.append("scop: Scop")
                c_args.append("scop.ptr_ccscop.current_node")
                start_idx = 1
            else:
                # Should not happen for these transformations but safer
                start_idx = 0

            for t, n in args[start_idx:]:
                # Map C types to Cython/Python types
                if t == "long":
                    py_type = "int"
                else:
                    py_type = t  # Fallback

                py_args.append(f"{n}: {py_type}")
                c_args.append(n)

            py_sig = ", ".join(py_args)
            c_call_args = ", ".join(c_args)

            f.write(f"@cython.ccall\n")
            f.write(f"def {py_name}({py_sig}):\n")
            f.write(f"    scop.ptr_ccscop.current_node = {name}({c_call_args})\n\n")

    print(f"Generated {H_FILE}, {PXD_FILE}, and {PY_FILE} with {len(funcs)} functions.")


if __name__ == "__main__":
    generate()
