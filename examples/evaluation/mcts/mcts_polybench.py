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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default="stencils/jacobi-2d")
    parser.add_argument(
        "--compiler_options", type=str, default="-DEXTRALARGE_DATASET -O3"
    )
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--rollouts", type=int, default=100)
    parser.add_argument("--seed", type=int, default=time.time())
    args = parser.parse_args()
    return args


def main():
    logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)
    # logger.info('message')
    args = get_args()
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
        TrEnum.SET_PARALLEL,
    }

    optimize_app(
        app,
        rollouts=args.rollouts,
        repeats=args.repeats,
        whitelist_transformations=allowed_transformations,
    )
    del app
    print("all done")


if __name__ == "__main__":
    main()
