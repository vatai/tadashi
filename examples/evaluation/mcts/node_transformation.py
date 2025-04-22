from tadashi import TrEnum

import mcts.base
import mcts.node_params
from mcts import config

# import MCTSNode


scop_idx = config["scop_idx"]


class MCTSNode_Transformation(mcts.base.MCTSNode):
    def set_up_children(self):
        if self.children:
            return
        node = self.app.scops[scop_idx].schedule_tree[self.action]
        available_transformations = self.filter_transformations(
            node.available_transformations
        )

        # print("AVAIL:", available_transformations)
        self.children = [
            mcts.node_params.MCTSNode_Params(parent=self, app=self.app, action=tr)
            for tr in available_transformations
        ]

    def roll(self, depth):
        self._number_of_visits += 1
        self.set_up_children()
        child = self.select_child()
        child.roll(depth)
