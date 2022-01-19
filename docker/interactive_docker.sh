#!/usr/bin/bash

docker run --rm -it \
       -v $(pwd):/workdir \
       -w /workdir \
       polytut:latest "$@"
       # --env LD_LIBRARY_PATH=/barvinok/.libs:/barvinok/pet/.libs:/barvinok/isl/.libs \
       # --env PYTHONPATH=/barvinok:/barvinok/pet/interface \
