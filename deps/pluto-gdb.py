#!/usb/bin/env python

# Link it to the same dir as pluto binary

import pluto_prog_printer

pluto_prog_printer.register_printers(gdb.current_objfile())
