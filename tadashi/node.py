from core import *


class Scop:
    def __init__(self, idx) -> None:
        self.idx = idx

    def get_current_node_from_ISL(self, parent):
        num_children = get_num_children(self.idx)
        inner_dim_names = get_dim_names(self.idx).decode().split(";")[:-1]
        dim_names = [t.split("|")[:-1] for t in inner_dim_names]
        node = Node(
            node_type=get_type(self.idx),
            type_str=get_type_str(self.idx),
            num_children=num_children,
            parent=parent,
            dim_names=dim_names,
            expr=get_expr(self.idx),
        )
        return node

    def traverse(self, nodes, parent):
        node = self.get_current_node_from_ISL(parent)
        print(f"{node=}")
        parent_idx = len(nodes)
        nodes.append(node)
        if not node.is_leaf():
            for c in range(node.num_children):
                goto_child(self.idx, c)
                node.children[c] = len(nodes)
                self.traverse(nodes, parent_idx)
                goto_parent(self.idx)

    def get_schedule_tree(self):
        nodes = []
        self.traverse(nodes, parent=-1)
        return nodes


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
