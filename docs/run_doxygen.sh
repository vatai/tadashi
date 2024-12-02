#!/bin/bash

INPUT="$(git rev-parse --show-toplevel)/src" PROJECT_NUMBER="$(git describe --tags | sed 's/^v//' | sed 's/-.*//')" doxygen Doxyfile
