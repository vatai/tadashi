#!/bin/env python

from enum import Enum, auto


class NodeType(Enum):
    """Type of the schedule tree node.

    Details: `ISL online user manual (Schedule Trees)`_.

    .. _ISL online user manual (Schedule Trees):
       https://libisl.sourceforge.io/user.html#Schedule-Trees
    """

    BAND = 0
    CONTEXT = auto()
    DOMAIN = auto()
    EXPANSION = auto()
    EXTENSION = auto()
    FILTER = auto()
    LEAF = auto()
    GUARD = auto()
    MARK = auto()
    SEQUENCE = auto()
    SET = auto()
