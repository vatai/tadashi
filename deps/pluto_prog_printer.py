#!/usb/bin/env python
import re

import gdb.printing


def get_string(s):
    main = str(s).split()[1:]
    return " ".join(main)[1:-1]


def deref(val):
    return val.dereference()


class PrinterBase:
    def __init__(self, val):
        self.val = val

    def get_array(self, key, nkey, fn):
        arr = self.val[key]
        rng = range(int(self.val[nkey]))
        return [fn(arr[i]) for i in rng]

    def print_members(self, members):
        result = ""
        for member in members:
            if len(member) == 3:
                tag, key, fn = member
                result += f"{tag}:{fn(self.val[key])}; "
            elif len(member) == 4:
                tag, key, nkey, fn = member
                result += f"{tag}:{self.get_array(key, nkey, fn)}; "
        return result


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
        members = [
            ("id", "id", int),  # OK!
            ("it", "iterators", "dim", get_string),  # check?!
            ("dom", "domain", deref),  # OK!
            ("t", "text", get_string),  # OK!
            ("iol", "is_orig_loop", "dim", int),  # OK!,
            # ("dim", "dim", int), # OK!
            ("do", "dim_orig", int),  # OK!
            ("t", "tile", int),  # OK!
            # ("tr", "trans", int),  # PlutoMatrix*
            ("evicted_hyp"),  # PlutoMatrix*
            ("ehp", "evicted_hyp_pos", int),  # OK!
            # tmp += f"{self.get_array('hyp_types','',id)};"  # PlutoHypType*
            ("ntl", "num_tiled_loops", int),  # OK!
            ("rx", "reads", "nreads", int),  # PlutoAccess *
            # tmp += f"{int(self.val['nreads']):2};" # OK!
            ("wx", "writes", "nwrites", int),  # PlutoAccess *
            # tmp += f"{int(self.val['nwrites']):2};"  # OK!
            ("sid", "scc_id", int),  # OK!
            ("cid", "cc_id", int),  # OK!
            ("ftd", "first_tile_dim", int),  # OK!
            ("ltd", "last_tile_dim", int),  # OK!
            ("typ", "type", int),  # PlutoStmtType
            ("plid", "ploop_id", int),  # OK!
            ("pcs", "parent_compute_stmt", int),  # statement*
            ("isd", "intra_stmt_dep_cst", int),  # PlutoConstraints*
            ("ps", "pstmt", int),  # pet_stmt*
        ]

        statement = self.print_members(members)
        return f"stmt: {statement}"


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

        return f"Cntr:{eqs}"


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("pluto_prog_printer")
    pp.add_printer("PlutoProg", "^plutoProg *$", PlutoProgPrinter)
    pp.add_printer("stmt", "^statement *$", StmtPrinter)
    pp.add_printer("pluto_constraint", "^pluto_constraints *$", ConstraintPrinter)
    return pp
