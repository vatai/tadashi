import tadashi.mcts.node_params

from .base import MCTSNode


class MCTSNode_Transformation(MCTSNode):
    def set_actions_transformations(self):
        self.children = [tadashi.mcts.node_params.MCTSNode_Params(parent=self, action=tr) for tr in self.action.available_transformations]

    def roll(self, depth):
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_transformations()
        child = self.select_child()
        child.roll(depth+1)
