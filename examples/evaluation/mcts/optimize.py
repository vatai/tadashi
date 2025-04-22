# from .node_root import MCTSNode_Root
from timeit import default_timer as timer

import mcts.node_root
from mcts import config


def optimize_app(
    app, rollouts=1, repeats=1, scop_idx=0, max_depth=2, whitelist_transformations=None
):
    config["rollouts"] = rollouts
    config["repeats"] = repeats
    config["max_depth"] = max_depth
    config["scop_idx"] = scop_idx
    if whitelist_transformations:
        config["whitelist_transformations"] = whitelist_transformations
    app.compile()
    print(config)
    start_time = timer()
    initial_time = app.measure(repeat=config["repeats"])
    end_time = timer()
    total_runtime = end_time - start_time
    config["timeout"] = total_runtime * 1.5 + 1
    print("initial time:", initial_time)
    root = tadashi.mcts.node_root.MCTSNode_Root(
        app=app, action="START", initial_time=initial_time
    )
    for rollout in range(config["rollouts"]):
        config["cnt_rollouts"] = rollout + 1
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
