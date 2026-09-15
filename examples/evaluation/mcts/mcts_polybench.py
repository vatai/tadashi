#!/bin/env python3

import random
import time

from tadashi.apps import Polybench

from mcts.optimize import optimize_app


def main(args):
    random.seed(args.seed)
    app = Polybench.from_args(args)
    print(app.scops[0].schedule_tree[0].yaml_str)
    print(f"{args.allow_omp=}")

    optimize_app(
        app,
        rollouts=args.rollouts,
        repeats=args.repeats,
        prefix=args.prefix,
    )
    print("all done")


if __name__ == "__main__":
    parser = Polybench.args_parser()
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--rollouts", type=int, default=100)
    parser.add_argument("--seed", type=int, default=time.time())
    parser.add_argument("--prefix", type=str, default="data")
    args = parser.parse_args()

    main(args)
