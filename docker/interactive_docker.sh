#!/usr/bin/bash

DOCKER_ARGS=(
    -v $(pwd)/../:$(dirname $(pwd))
    -w /$(dirname $(pwd))
    --env LD_LIBRARY_PATH=/barvinok/.libs:/barvinok/pet/.libs:/barvinok/isl/.libs
    --env PYTHONPATH=/barvinok:/barvinok/pet/interface
    polytut:latest "$@"
)

docker run --rm -it ${DOCKER_ARGS[@]}
