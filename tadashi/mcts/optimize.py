#from .node_root import MCTSNode_Root
import tadashi.mcts.node_root
from tadashi.mcts import config


def optimize_app(app, rollouts=1):
    config["rollouts"] = rollouts
    app.compile()
    print(config)
    initial_time = app.measure(repeat=config["repeats"])
    config["timeout"] = initial_time * 1.5 + 5
    print("initial time:", initial_time)
    root = tadashi.mcts.node_root.MCTSNode_Root(app=app, action="START", initial_time=initial_time)
    for rollout in range(config["rollouts"]):
        config["cnt_rollouts"] = rollout+1
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
