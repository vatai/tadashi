#!/bin/bash

ROOT="$(git rev-parse --show-toplevel)"
GIT_TAG="$(git describe --tags | sed 's/^v//' | sed 's/-.*//')"

export INPUT="$ROOT/src $ROOT/include"
export PROJECT_NUMBER="$GIT_TAG"

doxygen Doxyfile
