#!/bin/env python
from collections import namedtuple
from enum import Enum, StrEnum, auto

from .node_type import NodeType

SHOULD_NOT_HAPPEN = "This should not have happened. Please report an issue at https://github.com/vatai/tadashi/issues/"


class TransformInfo:
    pass


TRANSFORMATIONS: list[TransformInfo] = {}


class AstLoopType(Enum):
    """Possible values for `SET_LOOP_OPT`.

    `UNROLL` should be avoided unless the requirements in the
    `ISL Docs <https://libisl.sourceforge.io/user.html#AST-Generation-Options-Schedule-Tree>`_.
    are satisfied.

    """

    DEFAULT = 0
    ATOMIC = auto()
    UNROLL = auto()
    SEPARATE = auto()


class TrEnum(StrEnum):
    """Enums of implemented transformations.

    One of these enums needs to be passed to `Node.transform()` (with
    args) to perform the transformation.
    """

    TILE1D = auto()
    TILE2D = auto()
    TILE3D = auto()
    INTERCHANGE = auto()
    FUSE = auto()
    FULL_FUSE = auto()
    SPLIT = auto()
    FULL_SPLIT = auto()
    PARTIAL_SHIFT_VAR = auto()
    PARTIAL_SHIFT_VAL = auto()
    PARTIAL_SHIFT_PARAM = auto()
    FULL_SHIFT_VAR = auto()
    FULL_SHIFT_VAL = auto()
    FULL_SHIFT_PARAM = auto()
    SET_PARALLEL = auto()
    SET_LOOP_OPT = auto()

    def __repr__(self):
        return f"TrEnum.{self.value.upper()}"


LowerUpperBound = namedtuple(
    "LowerUpperBound",
    ["lower", "upper"],
    defaults=[None, None],
)
"""Integer interval description.

Lower and upper bounds for describing (integer) intervals of valid
arguments for transformations. `None` indicates no upper/lower bound.

"""


def register(tre: TrEnum):
    """Decorator to register transformations"""

    def _decorator(cls):
        TRANSFORMATIONS[tre] = cls
        return cls

    return _decorator


def _tilable(node: "Node", dim: int) -> bool:  # todo: try to move to Node
    for _ in range(dim):
        if node.node_type != NodeType.BAND:
            return False
        # if "tile" in node.label and "outer" in node.label:
        #     return False
        node = node.children[0]
    return True


@register(TrEnum.INTERCHANGE)
class InterchangeInfo(TransformInfo):
    func_name = "interchange"

    @staticmethod
    def valid(node: "Node"):
        return (
            node.node_type == NodeType.BAND
            and len(node.children) == 1
            and node.children[0].node_type == NodeType.BAND
        )


@register(TrEnum.TILE2D)
class Tile2DInfo(TransformInfo):
    func_name = "tile_2d"
    arg_help = ["Size1", "Size2"]

    @staticmethod
    def valid(node: "Node"):
        return _tilable(node, 2)

    @staticmethod
    def valid_args(node, size1, size2):
        return size1 > 1 and size2 > 1

    @staticmethod
    def available_args(node: "Node"):
        return [
            LowerUpperBound(lower=2, upper=None),
            LowerUpperBound(lower=2, upper=None),
        ]
