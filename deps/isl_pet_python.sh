#!/bin/bash

BARVINOK=build/barvinok
LD_LIBRARY_PATH=${BARVINOK}/.libs:${BARVINOK}/pet/.libs PYTHONPATH=${BARVINOK}:${BARVINOK}/pet/interface python "$@"
