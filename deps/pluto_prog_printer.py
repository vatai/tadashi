#!/usb/bin/env python
import functools
import re

import gdb.printing


def get_string(s):
    main = str(s).split()[1:]
    return " ".join(main)[1:-1]


def deref(val):
    return val.dereference() if bool(val) else ""


def sderef(val):
    return str(deref(val))


class PrinterBase:
    def __init__(self, val):
        self.val = val

    def get_array(self, key, nkey, fn, sep=None):
        """Print an array like member.

        Arguments:

            key[str]: The member where the data is.

            nkey[str]: A string of the form 'key1->key2->...->keyN',
                which describes the number of data elements which will
                be read.

            fn[Callable]: The transformation performed on each data
                element.

            sep[Optional[str]]: What is the separator for the
                elements.

        """
        arr = self.val[key]
        cur = self.val
        for k in nkey.split("->"):
            cur = cur[k]
        rng = range(int(cur))
        result = [fn(arr[i]) for i in rng]
        if sep:
            return sep.join(result)
        return result

    def print_members(self, members):
        result = ""
        for member in members:
            if len(member) == 3:
                tag, key, fn = member
                if fn == deref and int(self.val[key]) == 0:
                    continue
                result += f"{tag}:{fn(self.val[key])}; "
            elif len(member) == 5:
                tag, key, nkey, fn, sep = member
                sstr = sep if sep else ""
                result += f"{tag}:{sstr}{self.get_array(key, nkey, fn, sep)}; {sstr}"
            else:
                raise ValueError(f"Bad members: {members}")
        return result


class PlutoProgPrinter(PrinterBase):
    def to_string(self):
        """
        $1 = {
          OK: stmts = 0x555555a97730, nstmts = 2,
          TODO: deps = 0x555555ab7b90, ndeps = 6,
          OK: transdeps = 0x0, ntransdeps = 0,
          OK: data_names = 0x555555a96260, num_data = 3,
          params = 0x555555a96280,
          num_hyperplanes = 3,
          ddg = 0x0,
          fcg = 0x0,
          hProps = 0x555555aaf780,
          nvar = 1,
          npar = 1,
          param_context = 0x555555a91060,
          decls = 0x7ffff3bdb010 "",
          codegen_context = 0x555555a97610,
          globcst = 0x0,
          evicted_hyp_pos = 0,
          is_diamond_tiled = false,
          num_parameterized_loops = -1,
          num_stmts_to_be_coloured = 0,
          scaled_dims = 0x0,
          total_coloured_stmts = 0x0,
          coloured_dims = 0,
          mipTime = 0,
          ilpTime = 0,
          cst_solve_time = 0,
          cst_const_time = 0,
          cst_write_time = 0,
          scaling_cst_sol_time = 0,
          skew_time = 0,
          stencil_check_time = 0,
          fcg_const_time = 0,
          fcg_colour_time = 0,
          fcg_dims_scale_time = 0,
          fcg_update_time = 0,
          fcg_cst_alloc_time = 0,
          tss_time = 0,
          num_lp_calls = 0,
          context = 0x555555a90510
        }
        """
        members = [
            ("stmts", "stmts", "nstmts", sderef, "\n"),  # OK!
            ("deps", "deps", "ndeps", sderef, "\n"),
            ("tdeps", "transdeps", "ntransdeps", sderef, "\n"),  # zero
            ("dnames", "data_names", "num_data", get_string, None),  # OK!
        ]
        statement = self.print_members(members)
        return f"{statement}"


class PlutoAccessPrinter(PrinterBase):
    def to_string(self):
        """
        typedef struct pluto_access {
        int sym_id;
        char *name;

        /* scoplib_symbol_p symbol; */

        PlutoMatrix *mat;
        } PlutoAccess;
        """
        name = get_string(self.val["name"])
        mat = sderef(self.val["mat"])
        return f"{name}{mat}"


class PlutoConstraintPrinter(PrinterBase):
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


class PlutoMatrixPrinter(PrinterBase):
    def to_string(self):
        buf = self.val["val"]
        cols = range(int(self.val["ncols"]))
        rows = range(int(self.val["nrows"]))
        alloc_ncols = int(self.val["alloc_ncols"])
        rows_strs = []
        for row in rows:
            row = [str(buf[row][i]) for i in cols]
            rows_strs.append(",".join(row))
        return f"{{{'|'.join(rows_strs)}}}"


class PlutoHypTypePrinter(PrinterBase):
    def to_string(self):
        typs = ["UNKNOWN", "LOOP", "TILE_SPACE_LOOP", "SCALAR"]
        return typs[int(self.val)]


class StmtPrinter(PrinterBase):
    def to_string(self):
        members = [
            ("id", "id", int),  # OK!
            ("it", "iterators", "dim", get_string, None),  # OK!
            ("dom", "domain", deref),  # OK!
            ("t", "text", get_string),  # OK!
            ("iol", "is_orig_loop", "dim", int, None),  # OK!,
            # ("dim", "dim", int), # OK!
            ("do", "dim_orig", int),  # OK!
            ("t", "tile", int),  # OK!
            ("tr", "trans", deref),  # OK!
            ("eh", "evicted_hyp", deref),  # OK!
            ("ehp", "evicted_hyp_pos", int),  # OK!
            ("hty", "hyp_types", "trans->nrows", str, None),  # OK!
            ("ntl", "num_tiled_loops", int),  # OK!
            ("rx", "reads", "nreads", sderef, None),  # OK!
            # ("nr", "nreads", int),  # OK!
            ("wx", "writes", "nwrites", sderef, None),  # OK!
            # ("nw", "nwrites", int),  # OK!
            ("sid", "scc_id", int),  # OK!
            ("cid", "cc_id", int),  # OK!
            ("ftd", "first_tile_dim", int),  # OK!
            ("ltd", "last_tile_dim", int),  # OK!
            ("typ", "type", int),  # PlutoStmtType NEXT?!
            ("plid", "ploop_id", int),  # OK!
            ("pcs", "parent_compute_stmt", deref),  # OK!
            ("isd", "intra_stmt_dep_cst", int),  # PlutoConstraints*
            ("ps", "pstmt", int),  # pet_stmt*
        ]

        return self.print_members(members)


class DepPrinter(PrinterBase):
    def to_string(self):
        members = [
            ("id", "id", int),  # OK!
            ("s-st", "src", int),  # OK!
            ("d-st", "dest", int),  # OK!
            ("s-ac", "src_acc", sderef),  # OK!
            ("d-ac", "dest_acc", sderef),  # OK!
            ("tmp", "dpolytope", sderef),  # OK!
            # ("tmp", "bounding_poly", sderef),  # OK!
        ]

        return "foobar" + self.print_members(members)


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("pluto_prog_printer")
    pp.add_printer("PlutoProg", "^plutoProg *$", PlutoProgPrinter)
    pp.add_printer("stmt", "^statement *$", StmtPrinter)
    pp.add_printer("pluto_constraint", "^pluto_constraints *$", PlutoConstraintPrinter)
    pp.add_printer("pluto_matrix", "^pluto_matrix *$", PlutoMatrixPrinter)
    pp.add_printer("pluto_access", "^pluto_access *$", PlutoAccessPrinter)
    pp.add_printer("hyptype", "^hyptype *$", PlutoHypTypePrinter)
    pp.add_printer("dependence", "^dependence *$", DepPrinter)
    return pp
