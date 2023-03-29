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

        members = [
            ("id", "id", int),
            ("it", "iterators", "dim", get_string),
            ("dom", "domain", deref),
            ("t", "text", get_string),
            ("iol", "is_orig_loop", "dim", int),
            # ("dim", "dim", int) # OK!
        ]
        tmp = ""
        tmp += f"id:{int(self.val['id'])}; "
        tmp += f"it:{self.get_array('iterators', 'dim', get_string)};"  # check
        tmp += f"dom:{self.val['domain'].dereference()}; "
        tmp += f"{get_string(self.val['text'])};"  # OK!
        tmp += f"{self.get_array('is_orig_loop', 'dim',  int)};"  # check
        # tmp += f"d{int(self.val['dim']):2};" # OK!

        tmp += f"do{int(self.val['dim_orig']):2};"  # OK!
        tmp += f"t{int(self.val['tile']):2};"  # OK!
        tmp += f"tr{int(self.val['trans'])};"  # PlutoMatrix*
        tmp += f"eh{int(self.val['evicted_hyp'])};"  # PlutoMatrix*
        tmp += f"ehp{int(self.val['evicted_hyp_pos']):2};"  # OK!
        # tmp += f"{self.get_array('hyp_types','',id)};"  # PlutoHypType*
        tmp += f"ntl{int(self.val['num_tiled_loops']):2};"  # OK!
        tmp += f"rx:{self.get_array('reads', 'nreads', int)};"  # PlutoAccess *
        # tmp += f"{int(self.val['nreads']):2};" # OK!
        tmp += f"wx:{self.get_array('writes', 'nwrites', int)};"  # PlutoAccess *
        # tmp += f"{int(self.val['nwrites']):2};"  # OK!
        tmp += f"sid{int(self.val['scc_id']):2};"  # OK!
        tmp += f"cid{int(self.val['cc_id']):2};"  # OK!
        tmp += f"ftd{int(self.val['first_tile_dim']):02};"  # OK!
        tmp += f"ltd{int(self.val['last_tile_dim']):02};"  # OK!
        tmp += f"typ{int(self.val['type']):2};"  # PlutoStmtType
        tmp += f"plid{int(self.val['ploop_id']):2};"  # OK!
        tmp += f"pcs{int(self.val['parent_compute_stmt']):2};"  # statement*
        tmp += f"isd{self.val['intra_stmt_dep_cst']};"  # PlutoConstraints*
        tmp += f"ps{int(self.val['pstmt'])};"  # pet_stmt*

        line1 = f"Stmt: |{tmp}|"

        line2 = "Stmt: |"
        for member in members:
            if len(member) == 3:
                tag, key, fn = member
                line2 += f"{tag}:{fn(self.val[key])}; "
            elif len(member) == 4:
                tag, key, nkey, fn = member
                line2 += f"{tag}:{self.get_array(key, nkey, fn)}; "
        return f"{line1}\n{line2}\n"


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
