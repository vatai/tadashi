#!/bin/env python
import logging
import os

from .scop import TrEnum

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
