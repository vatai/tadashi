#!/usb/bin/env python
import re


class StmtPrinter(object):
    "Print Stmt"

    def __init__(self, val):
        self.val = val

    def to_string(self):
        text = str(self.val["text"])
        return f"StmtPrinter: {text}"

    def display_hint(self):
        return "plutoProg hint!!!"


def stmt_lookup_function(val):
    """Lookup Stmt"""
    lookup_tag = str(val.type)
    if lookup_tag is None:
        return None
    if re.match("^Stmt *$", lookup_tag):
        return StmtPrinter(val)
    return None


class PlutoProgPrinterOld(object):
    "Print plutoProg"

    def __init__(self, val):
        self.val = val

    def to_string(self):
        nstmts = int(self.val["nstmts"])
        stmts = self.val["stmts"]
        results = "\n" + "\n".join([str(stmts[i].dereference()) for i in range(nstmts)])
        return f"foobar ({nstmts}): {results}"

    def display_hint(self):
        return "plutoProg hint!!!"


def pluto_prog_lookup_function_old(val):
    """Look up PlutoProg"""
    lookup_tag = str(val.type)
    if lookup_tag is None:
        return None
    if re.match("^PlutoProg *$", lookup_tag):
        return PlutoProgPrinterOld(val)
    return None


class PlutoProgPrinter(object):
    "Print plutoProg"

    def __init__(self, val, fn):
        self.val = val
        self.fn = fn

    def to_string(self):
        nstmts = int(self.val["nstmts"])
        stmts = self.val["stmts"]
        results = "\n" + "\n".join([str(stmts[i].dereference()) for i in range(nstmts)])
        return f"foobar ({nstmts}): {results}"

    def display_hint(self):
        return "plutoProg hint!!!"


def pluto_prog_lookup_function(val):
    """Look up PlutoProg"""
    lookup_tag = str(val.type)
    if lookup_tag is None:
        return None
    if re.match("^PlutoProg *$", lookup_tag):
        return PlutoProgPrinter(val, None)
    return None


def register_printers(objfile):
    """Register pritty printers"""
    objfile.pretty_printers.append(pluto_prog_lookup_function)
    objfile.pretty_printers.append(stmt_lookup_function)
