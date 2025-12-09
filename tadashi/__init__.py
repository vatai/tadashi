#!/bin/env python
from enum import Enum, StrEnum, auto

SHOULD_NOT_HAPPEN = "This should not have happened. Please report an issue at https://github.com/vatai/tadashi/issues/"


class TransformInfo:
    pass


TRANSFORMATIONS: list[TransformInfo] = []


class TrEnum(StrEnum):
    INTERCHANGE = auto()


def register(enum: TrEnum):
    """Decorator to register transformations"""

    def _decorator(cls):
        TRANSFORMATIONS.append(cls)
        return cls

    return _decorator


@register(TrEnum.INTERCHANGE)
class InterchangeInfo(TransformInfo):
    pass
