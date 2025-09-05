from itertools import product

from tadashi import TRANSFORMATIONS, LowerUpperBound, TrEnum

import mcts.node_node
from mcts import config

from .base import MCTSNode

scop_idx = config["scop_idx"]


class MCTSNode_Params(MCTSNode):

    def get_args(self):
        node = self.app.scops[scop_idx].schedule_tree[self.parent.action]
        if self.action == TrEnum.SET_PARALLEL:
            return [[0]]
        tiles = [TrEnum.TILE1D, TrEnum.TILE2D, TrEnum.TILE3D]
        if self.action in tiles:
            rep = 1 + tiles.index(self.action)
            return [[2**x] * rep for x in range(5, 10)]
        return node.get_args(self.action, -5, 5)

    # TODO: perhaps implementing tail recursion here for var len params
    # also maybe better to make children a dictionary, so that we can add dynamically
    # TODO: this can be done lazily, if too many params
    def set_up_children(self):
        param_sets = self.get_args()
        if self.children is None:
            self.children = [
                mcts.node_node.MCTSNode_Node(parent=self, app=self.app, action=p)
                for p in param_sets
            ]

    def roll(self, depth):
        # print("select params")
        self._number_of_visits += 1
        self.set_up_children()
        child = self.select_child()
        child.evaluate()
        if depth < config["max_depth"]:
            child.roll(depth + 1)
