import tadashi.mcts.node_params
from tadashi import TrEnum

from .base import MCTSNode


class MCTSNode_Transformation(MCTSNode):
    def set_up_children(self):
        if self.children:
            return
        node = self.app.scops[0].schedule_tree[self.action]
        available_transformations = self.get_ISL_node_transformations(node)

        # print("AVAIL:", available_transformations)
        self.children = [
            tadashi.mcts.node_params.MCTSNode_Params(
                parent=self, app=self.app, action=tr
            )
            for tr in available_transformations
        ]

    def roll(self, depth):
        self._number_of_visits += 1
        self.set_up_children()
        child = self.select_child()
        child.roll(depth + 1)