#!/usb/bin/env python

# Link it to the same dir as pluto binary

import gdb.printing

import pluto_prog_printer

# pluto_prog_printer.register_printers(gdb.current_objfile())
gdb.printing.register_pretty_printer(
    gdb.current_objfile(),
    pluto_prog_printer.build_pretty_printer(),
)
