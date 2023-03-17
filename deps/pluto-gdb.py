#!/usb/bin/env python
import pluto_prog_printer

pluto_prog_printer.register_printers(gdb.current_objfile())
