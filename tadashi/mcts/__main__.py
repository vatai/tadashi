import argparse
import logging
import random
from pathlib import Path
from uuid import uuid4

# from tadashi import TrEnum
from tadashi.apps import Polybench, Simple
from tadashi.mcts import TimestampedJsonLogger
from tadashi.mcts.node_node import MCTSNode_Node


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
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)
    # logger.info('message')
    args = get_args()
#    setattr(Simple, "clone", clone_simple)
#    setattr(Polybench, "clone", clone_poly)
    random.seed(18)  # good seed that finds interchange right away for two loops
    # random.seed(21) # some errors
    base = "examples/polybench"
    app = Polybench(
        args.benchmark,
        base,
        compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
    )

    print(app.scops[0].schedule_tree[0].yaml_str)
    # return
    app.compile()
    initial_time = app.measure()
    # print("initial time:", initial_time)
    # Try do transformations manually
    # trs = [[0, 3, TrEnum.INTERCHANGE]]
    # app.transform_list(trs)
    # new_app = app.generate_code()
    # new_app.compile()
    # new_time = new_app.measure()
    # print("optimized time:", new_time)
    # with Simple(lalala) as app:
    # do things
    # app2 = app.generate_code()
    # app3 = app2.generate_code()
    # app4 = app3.generate_code()
    root = MCTSNode_Node(app=app, action="START", initial_time=initial_time)
    root.logger = TimestampedJsonLogger(app.source.name)
    root.logger.log(1, [], app.source.name)
    root.speedup = 1
    for rollout in range(15):
        print(f"---- doing rollout {rollout}")
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
