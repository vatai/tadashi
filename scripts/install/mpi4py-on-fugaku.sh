#!/bin/bash

env MPICC=mpifcc pip install mpi4py --no-cache-dir --no-binary mpi4py

# RUNNING:
# export LD_PRELOAD=/usr/lib/FJSVtcs/ple/lib64/libpmix.so
# mpiexec -n 8 python3 mpi-sample.py # for example
