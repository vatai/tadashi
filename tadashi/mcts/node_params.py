from itertools import product

import tadashi.mcts.node_node
from tadashi import TRANSFORMATIONS, LowerUpperBound, TrEnum
from tadashi.mcts import config

from .base import MCTSNode

scop_idx = config["scop_idx"]


class MCTSNode_Params(MCTSNode):

    # OK let us do the following here
    # be tail-recursing list of params until it is empty
    # then do eval and continue back to the node selection

    # But for now let's roll with default params
    @staticmethod
    def expand_lub(lub):
        if isinstance(lub, list):
            return lub
        if isinstance(lub, range):
            return lub
        assert isinstance(lub, LowerUpperBound), f"{type(lub)=}"
        lb, ub = lub
        if lb is None:
            lb = -5
        if ub is None:
            ub = 5
        return list(range(lb, ub))

    # @staticmethod
    def get_args(self):
        tr = self.action
        tr_obj = TRANSFORMATIONS[tr]
        node = self.app.scops[scop_idx].schedule_tree[self.parent.action]
        # args = self.get_args(tr_obj, node)
        # return args
        arg_groups = tr_obj.available_args(node)
        if not arg_groups:
            return [[]]
        # print(arg_groups)
        lubs = [MCTSNode_Params.expand_lub(lub) for lub in arg_groups]
        # print(lubs)
        expanded = list(product(*lubs))
        if isinstance(expanded[0][0], list):
            expanded = [[*trp[0], trp[1]] for trp in expanded]
        # print(expanded)
        return expanded

    # TODO: perhaps implementing tail recursion here for var len params
    # also maybe better to make children a dictionary, so that we can add dynamically
    # TODO: this can be done lazily, if too many params
    def set_up_children(self):
        param_sets = self.get_args()
        if self.children is None:
            self.children = [
                tadashi.mcts.node_node.MCTSNode_Node(
                    parent=self, app=self.app, action=p
                )
                for p in param_sets
            ]

    def roll(self, depth):
        # print("select params")
        self._number_of_visits += 1
        self.set_up_children()
        child = self.select_child()
        child.evaluate()
        if depth < 7:
            child.roll(depth + 1)
