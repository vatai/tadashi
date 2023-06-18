#!/bin/bash

echo ${BASH_SOURCE[0]}
BARVINOK=build/barvinok
export LD_LIBRARY_PATH=${BARVINOK}/.libs:${BARVINOK}/pet/.libs${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PYTHONPATH=${BARVINOK}:${BARVINOK}/pet/interface${PYTHONPATH:+:${PYTHONPATH}}
python "$@"
