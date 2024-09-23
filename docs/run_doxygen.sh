#!/bin/bash

INPUT="$(git rev-parse --show-toplevel)/src" PROJECT_NUMBER="x$(git describe --tags | sed 's/^v//' | sed 's/-.*//')" doxygen Doxyfile
