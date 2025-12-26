#!/bin/bash

set -e
rm -f *.whl
cp ../../../wheelhouse/*.whl  .
docker build . -t tadashi-fresh
docker run -v ../../..:/tadashi  --rm tadashi-fresh:latest python3 /tadashi/examples/end2end.py
