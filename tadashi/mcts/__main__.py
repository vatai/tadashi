from tadashi.apps import Polybench, Simple
from tadashi.mcts import MCTSNode_Node

if __name__ == "__main__":
    # app = Polybench("linear-algebra/blas/gemm", "./examples/polybench/", compiler_options=["-D", "LARGE_DATASET"])
    app = Simple("./examples/inputs/simple/two_loops.c")
    app.compile()
    initial_time = app.measure()
    print("initial time:", initial_time)
    root = MCTSNode_Node(app=app, action="START")
    root.select_node()
    print("samples tree as follows:")
    root.print()