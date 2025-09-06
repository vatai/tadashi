#!/bin/env python

import argparse
import logging
import random
import time
from pathlib import Path
from timeit import repeat

from tadashi import TrEnum
from tadashi.apps import Polybench, Simple

from mcts import config
from mcts.optimize import optimize_app


def main(args):
    logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)
    # logger.info('message')
    random.seed(args.seed)
    app = Polybench(
        args.benchmark,
        compiler_options=args.compiler_options.split(" "),
    )
    print(app.scops[0].schedule_tree[0].yaml_str)
    allowed_transformations = {
        TrEnum.TILE1D,
        TrEnum.TILE2D,
        TrEnum.TILE3D,
        TrEnum.INTERCHANGE,
        # TrEnum.FUSE,
        TrEnum.FULL_FUSE,
        TrEnum.SPLIT,
        TrEnum.FULL_SPLIT,
    }
    print(f"{args.allow_omp=}")
    if args.allow_omp:
        allowed_transformations.add(TrEnum.SET_PARALLEL)

    optimize_app(
        app,
        rollouts=args.rollouts,
        repeats=args.repeats,
        whitelist_transformations=allowed_transformations,
        prefix=args.prefix,
    )
    del app
    print("all done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=str, default="stencils/jacobi-2d")
    parser.add_argument(
        "--compiler_options", type=str, default="-DEXTRALARGE_DATASET -O3"
    )
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--rollouts", type=int, default=100)
    parser.add_argument("--seed", type=int, default=time.time())
    parser.add_argument(
        "--allow-omp", type=bool, default=False, action=argparse.BooleanOptionalAction
    )
    parser.add_argument("--prefix", type=str, default="data")
    args = parser.parse_args()

    main(args)
