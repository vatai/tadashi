#!/bin/env python
import logging
import os
from enum import StrEnum, auto


class TrEnum(StrEnum):
    """Enums of implemented transformations.

    One of these enums needs to be passed to `Node.transform()` (with
    args) to perform the transformation.
    """

    TILE_1D = auto()
    TILE_2D = auto()
    TILE_3D = auto()
    INTERCHANGE = auto()
    FULL_FUSE = auto()
    FUSE = auto()
    FULL_SPLIT = auto()
    SPLIT = auto()
    SCALE = auto()
    FULL_SHIFT_VAL = auto()
    PARTIAL_SHIFT_VAL = auto()
    FULL_SHIFT_VAR = auto()
    PARTIAL_SHIFT_VAR = auto()
    FULL_SHIFT_PARAM = auto()
    PARTIAL_SHIFT_PARAM = auto()
    SET_PARALLEL = auto()
    SET_LOOP_OPT = auto()


# Format
FORMAT = "[%(filename)s:%(lineno)s - %(name)s::%(funcName)s() ] %(message)s"

# Log level
default = "CRITICAL"
log_level = os.getenv("LOG_LEVEL", default).upper()
valid_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
if log_level not in valid_levels:
    logging.warning(f"Invalid log level: {log_level}. Defaulting to {default}.")
    log_level = default

level = logging.getLevelNamesMapping()[log_level]
logging.basicConfig(level=level, format=FORMAT)
