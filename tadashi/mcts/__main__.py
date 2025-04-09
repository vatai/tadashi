import argparse
import logging
import random
import time

# from tadashi import TrEnum
from tadashi.apps import Polybench, Simple
from tadashi.mcts import TimestampedJsonLogger, config
from tadashi.mcts.node_node import MCTSNode_Node

# from pathlib import Path
# from uuid import uuid4


# TODO (Emil): move it to apps later, just don't want to deal with merges now
# def clone_simple(self):
#     file_path = Path(self.source)
#     directory = file_path.parent
#     extension = file_path.suffix  # Get the file extension
#     if (
#         not directory
#     ):  # if the given file_path is just a filename in the current directory
#         directory = pathlib.Path(".")  # use the current directory
#     new_filename = f"clone_{uuid4()}.{extension}"
#     new_app = self.generate_code(directory / new_filename, ephemeral=True)
#     # new_app.remove_source()
#     return new_app


# def clone_poly(self):
#     new_app = self.generate_code(ephemeral=True)
#     # print("SOURCE")
#     # print(new_app.source)
#     # new_app.remove_source()
#     return new_app


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=str, default="stencils/jacobi-2d")
    parser.add_argument("--compiler_options", type=str, default="-DEXTRALARGE_DATASET -O3")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--rollouts", type=int, default=100)
    parser.add_argument("--seed", type=int, default=time.time())
    args = parser.parse_args()
    config.update(vars(args))
    return args


def main():
    logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)
    # logger.info('message')
    args = get_args()
#    setattr(Simple, "clone", clone_simple)
#    setattr(Polybench, "clone", clone_poly)
    random.seed(args.seed)  # good seed that finds interchange right away for two loops
    # random.seed(21) # some errors
    base = "examples/polybench"
    # app = Simple("./examples/inputs/simple/two_loops.c")
    # app = Simple("./examples/inputs/simple/gemm.c", compiler_options=["-O3"],)
    # app = Simple("./examples/inputs/simple/jacobi/base.c", compiler_options=["-O3"],)
    app = Polybench(
        args.benchmark,
        base,
        compiler_options=args.compiler_options.split(" "),
    )

    print(app.scops[0].schedule_tree[0].yaml_str)
    # return
    app.compile()
    print(config)
    initial_time = app.measure(repeat=config["repeats"])
    config["timeout"] = initial_time * 1.5
    print("initial time:", initial_time)
    root = MCTSNode_Node(app=app, action="START", initial_time=initial_time)
    root.logger = TimestampedJsonLogger(app.source.name)
    root.logger.log(1, [], app.source.name)
    root.speedup = 1
    for rollout in range(config["rollouts"]):
        print(f"\n---- doing rollout {rollout}")
        root.roll()
    print("\n**************************\n")
    print("sampled tree as follows:\n")
    root.set_best()
    root.print()

    print()
    print("BEST:")
    root.print_best()
    root.show_best_source()
    del root
    del app
    print("all done")


if __name__ == "__main__":
    main()
