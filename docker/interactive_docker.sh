#!/usr/bin/bash

DOCKER_ARGS=(
    run --rm -it
    # -v $(pwd):/workdir
    -v $(pwd)/..:/workdir
    # -w /workdir
    -w /barvinok
    polytut:latest "$@"
    # --env LD_LIBRARY_PATH=/barvinok/.libs:/barvinok/pet/.libs:/barvinok/isl/.libs
    # --env PYTHONPATH=/barvinok:/barvinok/pet/interface
)
docker ${DOCKER_ARGS[@]}
