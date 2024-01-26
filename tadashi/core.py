from ctypes import (CDLL, POINTER, Structure, c_char_p, c_int, c_long,
                    c_longlong, c_size_t)
from pathlib import Path

so_path = Path(__file__).parent.parent / "build/libctadashi.so"
_tadashi = CDLL(so_path)


########################################

get_num_scops = _tadashi.get_num_scops
get_num_scops.argtypes = [c_char_p]

goto_parent = _tadashi.goto_parent

goto_child = _tadashi.goto_child
goto_child.argtypes = [c_long, c_long]

get_num_children = _tadashi.get_num_children
get_num_children.argtypes = [c_long]

get_dim_names = _tadashi.get_dim_names
get_dim_names.restype = c_char_p
get_dim_names.argtypes = [c_long]

get_schedule_yaml = _tadashi.get_schedule_yaml
get_schedule_yaml.restype = c_char_p
get_schedule_yaml.argtypes = [c_long]

get_type = _tadashi.get_type
get_type.restype = c_int
get_type.argtypes = [c_long]

get_type_str = _tadashi.get_type_str
get_type_str.restype = c_char_p
get_type_str.argtypes = [c_long]

get_expr = _tadashi.get_expr
get_expr.restype = c_char_p
get_expr.argtypes = [c_long]

free_scops = _tadashi.free_scops
