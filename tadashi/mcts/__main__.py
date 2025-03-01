from tadashi.apps import Polybench
from tadashi.mcts import MCTSNode

if __name__ == "__main__":
    app = Polybench("linear-algebra/blas/gemm", "./examples/polybench/", compiler_options=["-D", "LARGE_DATASET"])
    root = MCTSNode(app=app, action="START")
    root.select_node()
    print("samples tree as follows:")
    root.print()