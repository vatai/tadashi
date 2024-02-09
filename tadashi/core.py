# Authors: Aleksandr DROZD, Emil VATAI
# Date: 2024, January

# This file is the "Python side" between the C and Python code of
# tadashi.

from ctypes import CDLL, c_char_p, c_int, c_size_t
from pathlib import Path

so_path = Path(__file__).parent.parent / "build/libctadashi.so"
_tadashi = CDLL(str(so_path))


get_num_scops = _tadashi.get_num_scops
get_num_scops.argtypes = [c_char_p]
get_num_scops.restype = c_int

free_scops = _tadashi.free_scops

get_type = _tadashi.get_type
get_type.argtypes = [c_size_t]
get_type.restype = c_int

get_type_str = _tadashi.get_type_str
get_type_str.argtypes = [c_size_t]
get_type_str.restype = c_char_p

get_num_children = _tadashi.get_num_children
get_num_children.argtypes = [c_size_t]
get_num_children.restype = c_size_t

goto_parent = _tadashi.goto_parent
goto_parent.argtypes = [c_size_t]

goto_child = _tadashi.goto_child
goto_child.argtypes = [c_size_t, c_size_t]

get_expr = _tadashi.get_expr
get_expr.argtypes = [c_size_t]
get_expr.restype = c_char_p

get_dim_names = _tadashi.get_dim_names
get_dim_names.argtypes = [c_size_t]
get_dim_names.restype = c_char_p

get_schedule_yaml = _tadashi.get_schedule_yaml
get_schedule_yaml.argtypes = [c_size_t]
get_schedule_yaml.restype = c_char_p
