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
        id = int(self.val["id"])
        domain = str(self.val["domain"].dereference())
        # iterators ??
        text = get_string(self.val["text"])
        is_orig_loop = int(self.val["is_orig_loop"])

        dim = int(self.val["dim"])
        dim_orig = int(self.val["dim_orig"])
        tile = int(self.val["tile"])
        trans = int(self.val["trans"])
        evicted_hyp = int(self.val["evicted_hyp"])
        evicted_hyp_pos = int(self.val["evicted_hyp_pos"])
        hyp_types = int(self.val["hyp_types"])
        num_tiled_loops = int(self.val["num_tiled_loops"])
        reads = int(self.val["reads"])
        nreads = int(self.val["nreads"])
        writes = int(self.val["writes"])
        nwrites = int(self.val["nwrites"])
        scc_id = int(self.val["scc_id"])
        cc_id = int(self.val["cc_id"])
        first_tile_dim = int(self.val["first_tile_dim"])
        last_tile_dim = int(self.val["last_tile_dim"])
        type = int(self.val["type"])
        ploop_id = int(self.val["ploop_id"])
        parent_compute_stmt = int(self.val["parent_compute_stmt"])
        intra_stmt_dep_cst = int(self.val["intra_stmt_dep_cst"])
        pstmt = int(self.val["pstmt"])

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
    # pp.add_printer("stmt", "^statement *$", StmtPrinter)
    pp.add_printer("pluto_constraint", "^pluto_constraints *$", ConstraintPrinter)
    return pp
