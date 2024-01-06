from ctypes import (CDLL, POINTER, Structure, c_char_p, c_int, c_longlong,
                    c_size_t)
from pathlib import Path

########################################


class cell_t(Structure):
    pass


cell_t._fields_ = [("name", c_longlong), ("next", POINTER(cell_t))]

so_path = Path(__file__).parent.parent / "build/libctadashi.so"
print(so_path)
_tadashi = CDLL(so_path)

_tadashi.foo.restype = POINTER(cell_t)
_tadashi.foo.argtypes = [c_size_t]
foo = _tadashi.foo

_tadashi.bar.restype = c_size_t
_tadashi.bar.argtypes = [POINTER(cell_t)]
bar = _tadashi.bar

c = foo(10)
# print(c)
# print(bar(c))

########################################

scan_source = _tadashi.scan_source
scan_source.argtypes = [c_char_p]

scan_source(b"./examples/depnodep.c")

print("PYTHON DONE")
