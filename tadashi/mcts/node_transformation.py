from zoneinfo import available_timezones

import tadashi.mcts.node_params
from tadashi import TrEnum

from .base import MCTSNode


class MCTSNode_Transformation(MCTSNode):
    def set_actions_transformations(self):
        node = self.app.scops[0].schedule_tree[self.action]
        available_transformations = self.get_ISL_node_transformations(node)

        # print("AVAIL:", available_transformations)
        self.children = [
            tadashi.mcts.node_params.MCTSNode_Params(
                parent=self, app=self.app.clone(), action=tr
            )
            for tr in available_transformations
        ]

    def roll(self, depth):
        # print("select transform")
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_transformations()
        if self.children:
            child = self.select_child()
            # print("selected transform as tr")
            child.roll(depth + 1)
        else:
            print("HOW COME WE CHOOSE NODE WITHOUT TRANSFORMS??")
            print("selected node:", self.action)
            nodes = self.app.scops[0].schedule_tree
            print(nodes[self.action])
            raise Exception()
            self.update_stats(-1)
