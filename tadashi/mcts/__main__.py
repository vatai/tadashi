from tadashi import TrEnum
from tadashi.apps import Polybench, Simple
from tadashi.mcts import MCTSNode_Node

if __name__ == "__main__":
    # app = Polybench("linear-algebra/blas/gemm", "./examples/polybench/", compiler_options=["-D", "LARGE_DATASET"])
    app = Simple("./examples/inputs/simple/two_loops.c")
    print(app.scops[0].schedule_tree[0].yaml_str)
    app.compile()
    initial_time = app.measure()
    print("initial time:", initial_time)
    # Try do transformations manually
    trs = [[0, 3, TrEnum.INTERCHANGE]]
    app.transform_list(trs)
    new_app = app.generate_code()
    new_app.compile()
    new_time = new_app.measure()
    print("optimized time:", new_time)

    #root = MCTSNode_Node(app=app, action="START")
    #root.select_node()
    #print("samples tree as follows:")
    #root.print()