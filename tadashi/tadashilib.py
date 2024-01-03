from ctypes import CDLL, POINTER, Structure, c_int, c_longlong, c_size_t


class cell_t(Structure):
    pass


cell_t._fields_ = [("name", c_longlong), ("next", POINTER(cell_t))]

_tadashi = CDLL("./libmain.so")

_tadashi.foo.restype = POINTER(cell_t)
_tadashi.foo.argtypes = [c_size_t]
foo = _tadashi.foo

_tadashi.bar.restype = c_int
_tadashi.bar.argtypes = [POINTER(cell_t)]
bar = _tadashi.bar
