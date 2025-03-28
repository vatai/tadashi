from tadashi import TrEnum
from tadashi.apps import Polybench, Simple
from tadashi.mcts.node_node import MCTSNode_Node

if __name__ == "__main__":
    # app = Polybench("linear-algebra/blas/gemm", "./examples/polybench/", compiler_options=["-D", "LARGE_DATASET"])
    app = Simple("./examples/inputs/simple/two_loops.c")
    print(app.scops[0].schedule_tree[0].yaml_str)
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
    root = MCTSNode_Node(app=app, action="START", initial_time=initial_time)
    root.speedup = 1
    for rollout in range(100):
        print(f"doing rollout {rollout}")
        root.roll()
    print("sampled tree as follows:")
    root.print()
    del root
    del app
    print("all done")