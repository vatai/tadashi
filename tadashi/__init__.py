#!/bin/env python
from enum import Enum, StrEnum, auto

TRANSFORMATIONS = []  # : list["transformation"]


class TrEnum(StrEnum):
    INTERCHANGE = auto()


def register(enum: TrEnum):
    """Decorator to register transformations"""

    def _decorator(cls):
        TRANSFORMATIONS.append(cls)
        return cls

    return _decorator


class TransformInfo:
    pass


@register(TrEnum.INTERCHANGE)
class InterchangeInfo(TransformInfo):
    pass


print("=========================")
print(f"{TRANSFORMATIONS=}")
