import random
from itertools import product

import tadashi.mcts.node_node
from tadashi import TRANSFORMATIONS, LowerUpperBound, TrEnum

from .base import MCTSNode


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
        node = self.app.scops[0].schedule_tree[self.parent.action]
        # args = self.get_args(tr_obj, node)
        # return args
        arg_groups = tr_obj.available_args(node)
        if not arg_groups:
            return [[]]
        # print(arg_groups)
        lubs = [MCTSNode_Params.expand_lub(lub) for lub in arg_groups]
        # print(lubs)
        expanded = list(product(*lubs))
        # print(expanded)
        return expanded

    # TODO: perhaps implementing tail recursion here for var len params
    # also maybe better to make children a dictionary, so that we can add dynamically
    def roll(self, depth):
        # print("select params")
        self._number_of_visits += 1
        # TODO: this can be done lazily, if too many params
        param_sets = self.get_args()
        if self.children is None:
            self.children = [
                tadashi.mcts.node_node.MCTSNode_Node(
                    parent=self, app=self.app.clone(), action=p
                )
                for p in param_sets
            ]
        # print("children:", self.children[0].action)
        # params = self.parent.action.available_args(self.action)
        child = self.select_child()
        # print("select as ", child)
        child.evaluate()
        if depth < 7:
            child.roll(depth + 1)
