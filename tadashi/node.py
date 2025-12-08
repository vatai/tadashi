#!/bin/env python

from dataclasses import dataclass

from .node_type import NodeType


@dataclass
class Node:
    """Schedule node (Python representation)."""

    #: Pointer to the `Scop` object the node belongs to.
    scop: "Scop"

    #: Type of the node in the schedule tree.
    node_type: NodeType

    #: Number of children of the node in the schedule tree.
    num_children: int

    #: The index of the parent of the node in the schedule tree
    #: according to `Scop.schedule_tree`.
    parent_idx: int

    #: The index of the current node in `Scop.schedule_tree`.
    index: int

    #: A string identifying the node.
    label: str

    #: List of child indexes which determine the location of the node
    #: starting from the root.  See `Scop.locate`.
    location: list[int]

    #: Description of the band nodes (see `Scop.get_loop_signature`).
    loop_signature: list[dict]

    #: The ISL expression of the schedule node.
    expr: str

    #: Index of the children in `Scop.schedule_tree`.
    children_idx: list[str]

    @property
    def parent(self):
        """The node which is the parent of the current node."""
        return self.scop.schedule_tree[self.parent_idx]

    @property
    def children(self):
        """List of nodes which are the children of the current node."""
        return [self.scop.schedule_tree[i] for i in self.children_idx]

    def __repr__(self):
        """Textual representation of a node."""
        words = [
            "Node type:",
            f"{self.node_type},",
            f"{self.loop_signature},",
            f"{self.expr},",
            f"{self.location}",
        ]
        return " ".join(words)

    def locate(self):
        """Set the `current_node` to point to `self`."""
        self.scop.locate(self.location)
        return self.scop.get_current_node_from_ISL(None, None)

    def transform(self) -> bool:
        pass
