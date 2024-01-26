from core import *


def get_node(scop_idx, parent):
    num_children = get_num_children(scop_idx)
    inner_dim_names = get_dim_names(scop_idx).decode().split(";")[:-1]
    dim_names = [t.split("|")[:-1] for t in inner_dim_names]
    node = Node(
        node_type=get_type(scop_idx),
        type_str=get_type_str(scop_idx),
        num_children=num_children,
        parent=parent,
        dim_names=dim_names,
        expr=get_expr(scop_idx),
    )
    return node


class Node:
    def __init__(
        self,
        node_type,
        type_str,
        num_children,
        parent,
        dim_names,
        expr,
    ) -> None:
        self.node_type = node_type
        self.type_str = type_str
        self.num_children = num_children
        self.parent = parent
        self.dim_names = dim_names
        self.expr = expr
        self.children = [-1 for _ in range(num_children)]

    def __repr__(self):
        return f"Node type: {self.type_str}, {self.dim_names}, {self.expr}"

    def is_leaf(self):
        return self.node_type == 6
