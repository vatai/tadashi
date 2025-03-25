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
        assert isinstance(lub, LowerUpperBound)
        lb, ub = lub
        if lb is None:
            lb = -5
        if ub is None:
            ub = 5
        return list(range(lb, ub))

    @staticmethod
    def get_args(tr, node):
        arg_groups = tr.available_args(node)
        if not arg_groups:
            return [[]]
        # print(arg_groups)
        lubs = [MCTSNode_Params.expand_lub(lub) for lub in arg_groups]
        # print(lubs)
        expanded = list(product(*lubs))
        # print(expanded)
        return expanded

    def select_default_params(self):
        tr = self.action
        tr_obj = TRANSFORMATIONS[tr]
        node = self.app.scops[0].schedule_tree[self.parent.action]
        args = self.get_args(tr_obj, node)
        if args:
            args = random.choice(args)
        return args
        # tr = self.action
        # print("SELECTING PARAMS FOR", tr, type(tr))
        # if tr == TrEnum.TILE:
        #     tile_size = random.choice([2**x for x in range(5, 12)])
        #     print("RETURN FOR TILE")
        #     return [tile_size]
        # tr = TRANSFORMATIONS[tr]
        # node = self.app.scops[0].schedule_tree[self.parent.action]
        # lubs = tr.available_args(node=node)
        # args = []
        # for lub in lubs:
        #     if isinstance(lub, LowerUpperBound):
        #         lb, ub = lub
        #         if lb is None:
        #             lb = -5
        #         if ub is None:
        #             ub = 5
        #         tmp = list(range(lb, ub))
        #     else:
        #         tmp = [t.value for t in lub]
        #     args = list(product(args, tmp) if args else tmp)
        # args = list(args)
        # if args:
        #     args = random.choice(args)
        # return args

    # TODO: perhaps implementing tail recursion here for var len params
    # also maybe better to make children a dictionary, so that we can add dynamically
    def roll(self, depth):
        self._number_of_visits += 1
        # TODO: this can be done lazily, if too many params
        if self.children is None:
            # thould we do some eval here?
            self.children = [tadashi.mcts.node_node.MCTSNode_Node(parent=self,
                                                                  app=self.app,
                                                                  action=self.select_default_params())]
        # print("children:", self.children[0].action)
        # params = self.parent.action.available_args(self.action)
        #print(params)
        child = self.select_child()
        child.evaluate(depth + 1)
