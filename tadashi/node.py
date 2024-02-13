from core import (free_scops, get_dim_names, get_expr, get_num_children,
                  get_num_scops, get_type, get_type_str, goto_child,
                  goto_parent, reset_root, tile)


class Scop:
    """Single SCoP.

    In the .so file, there is a global `std::vecto` of `isl_scop`
    objects.  Objects of `Scop` (in python) represents a the
    `isl_scop` object by storing its index in the `std::vecto`.

    """

    def __init__(self, idx) -> None:
        self.idx = idx

    def get_current_node_from_ISL(self, parent, location):
        num_children = get_num_children(self.idx)
        inner_dim_names = get_dim_names(self.idx).decode().split(";")[:-1]
        dim_names = [t.split("|")[:-1] for t in inner_dim_names]
        node = Node(
            scop=self,
            node_type=get_type(self.idx),
            type_str=get_type_str(self.idx).decode("utf-8"),
            num_children=num_children,
            parent=parent,
            location=location,
            dim_names=dim_names,
            expr=get_expr(self.idx).decode("utf-8"),
        )
        return node

    def traverse(self, nodes, parent, path):
        node = self.get_current_node_from_ISL(parent, path)
        print(f"{node=}")
        parent_idx = len(nodes)
        nodes.append(node)
        if not node.is_leaf():
            for c in range(node.num_children):
                goto_child(self.idx, c)
                node.children[c] = len(nodes)
                self.traverse(nodes, parent_idx, path + [c])
                goto_parent(self.idx)

    def get_schedule_tree(self):
        reset_root(self.idx)
        nodes = []
        self.traverse(nodes, parent=-1, path=[])
        return nodes

    def locate(self, location):
        reset_root(self.idx)
        for c in location:
            goto_child(self.idx, c)

    def tile(self, tile_size):
        tile(self.idx, tile_size)


class Scops:
    """All SCoPs which belong to a given file.

    The object of type `Scops` is similar to a list."""

    def __init__(self, path):
        self.num_scops = get_num_scops(path)
        self.scops = [Scop(i) for i in range(self.num_scops)]

    def __len__(self):
        return self.num_scops

    def __getitem__(self, idx):
        return self.scops[idx]

    def __del__(self):
        free_scops()


class Node:
    LEAF_TYPE = 6

    def __init__(
        self,
        scop,
        node_type,
        type_str,
        num_children,
        parent,
        location,
        dim_names,
        expr,
    ) -> None:
        self.scop = scop
        self.node_type = node_type
        self.type_str = type_str
        self.num_children = num_children
        self.parent = parent
        self.dim_names = dim_names
        self.expr = expr
        self.children = [-1] * num_children
        self.location = location

    def __repr__(self):
        return f"Node type: {self.type_str}({self.node_type}), {self.dim_names}, {self.expr}, {self.location}"

    def is_leaf(self):
        return self.node_type == self.LEAF_TYPE

    def locate(self):
        self.scop.locate(self.location)
        return self.scop.get_current_node_from_ISL(None, None)

    def tile(self, tile_size):
        self.scop.locate(self.location)
        self.scop.tile(tile_size)
