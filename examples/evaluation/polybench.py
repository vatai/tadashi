import argparse
import os
import sys

from tadashi.apps import Polybench

def find_ml4t():
    ML4T = "ML4TADASHI"
    ml4tadashi = os.path.dirname(__file__)
    while not os.path.exists(os.path.join(ml4tadashi, ML4T)):
        ml4tadashi = os.path.dirname(ml4tadashi)
    print(f"{ml4tadashi=}")
    sys.path.append(ml4tadashi)
    print(f"{sys.path=}")
    ml4tadashi = os.path.join(ml4tadashi, ML4T)
    sys.path.append(ml4tadashi)
    print(f"{sys.path=}")

    global run
    from ML4TADASHI import run

tadashi_base = os.path.dirname(os.path.dirname(__file__))
base = os.path.join(tadashi_base, "polybench")


def main():
    find_ml4t()
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
