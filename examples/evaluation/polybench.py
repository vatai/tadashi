import argparse
import os
import sys

from tadashi.apps import Polybench

ml4tadashi = os.path.dirname(__file__)
ml4tadashi = os.path.dirname(ml4tadashi)
ml4tadashi = os.path.dirname(ml4tadashi)
sys.path.append(ml4tadashi)
ml4tadashi = os.path.join(ml4tadashi, "ML4TADASHI")
sys.path.append(ml4tadashi)

from ML4TADASHI import run

tadashi_base = os.path.dirname(os.path.dirname(__file__))
base = os.path.join(tadashi_base, "polybench")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark")
    args, unknown = parser.parse_known_args()
    print(f"{args.benchmark=}")
    translator = "Pet"
    kwargs = {"base": base, "translator": translator}
    kwargs["benchmark"] = args.benchmark
    run(Polybench, kwargs, unknown)


if __name__ == "__main__":
    main()
