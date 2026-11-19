#!/bin/bash

#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -L rscgrp=small
#PJM -L elapse=30:00
#PJM -L node=1
# #PJM --llio localtmp-size=40Gi
module load LLVM/llvmorg-21.1.0
python -u $ENTRYPOINT --benchmark="${BENCHMARK}" --root="${ROOT}"
