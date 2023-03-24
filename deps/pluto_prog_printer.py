#!/usb/bin/env python
import re

import gdb.printing


def get_string(s):
    main = str(s).split()[1:]
    return " ".join(main)[1:-1]


class PrinterBase:
    def __init__(self, val):
        self.val = val

    def get_array(self, key, nkey, fn):
        arr = self.val[key]
        rng = range(int(self.val[nkey]))
        return [fn(arr[i]) for i in rng]


class PlutoProgPrinter(PrinterBase):
    def to_string(self):
        nstmts = int(self.val["nstmts"])
        stmts = self.val["stmts"]
        stmts = "\n" + "\n".join(
            self.get_array("stmts", "nstmts", lambda t: str(t.dereference()))
        )
        return f"PlutoProg ({nstmts}): {stmts}"


class StmtPrinter(PrinterBase):
    def to_string(self):
        text = get_string(self.val["text"])
        domain = str(self.val["domain"].dereference())
        return f"Stmt: {text} \n{domain}"


class ConstraintPrinter(PrinterBase):
    def to_string(self):
        buf = self.val["buf"]
        ncols = int(self.val["ncols"])
        nrows = int(self.val["nrows"])
        names = self.get_array("names", "ncols", get_string)
        eqs = []
        for row in range(nrows):
            is_eq = "=" if bool(self.val["is_eq"][row]) else "<="
            base = row * int(self.val["alloc_ncols"])
            terms = [f"0{is_eq}"]
            terms += [
                f"{buf[base + i]}{names[i]}" for i in range(ncols) if int(buf[base + i])
            ]
            eqs.append("".join([(t if t[0] == "-" else f"+{t}") for t in terms]))

        return f"Constraint: {eqs}"


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("pluto_prog_printer")
    pp.add_printer("PlutoProg", "^plutoProg *$", PlutoProgPrinter)
    pp.add_printer("stmt", "^statement *$", StmtPrinter)
    pp.add_printer("pluto_constraint", "^pluto_constraints *$", ConstraintPrinter)
    return pp
