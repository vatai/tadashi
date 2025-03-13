import tadashi.mcts.node_transformation
from tadashi import TrEnum

from .base import MCTSNode


# This is a bit confusing, but the name implies that we are on a level where we are
# SELECTING node, maybe I should shift naming
class MCTSNode_Node(MCTSNode):

    def set_actions_from_nodes(self):
        nodes = self.app.scops[0].schedule_tree
        nodes_transformable = []
        for i in range(len(nodes)):
            if nodes[i].available_transformations:
                nodes_transformable.append(i)
        # TODO: do this lazily to avoid expensive cloning through code generation
            self.children = [tadashi.mcts.node_transformation.MCTSNode_Transformation(parent=self,
                                                                                      app=self.app,
                                                                                      action=node) for node in nodes_transformable]

    def evaluate(self, depth):
        print("measuring performance")
        self._number_of_visits += 1
        # cloned_app = self.app.generate_code()
        default_scop = 0
        node = self.parent.parent.action
        tr = self.parent.action
        args = self.action
        trs = [[default_scop, node, tr, *args]]
        print("selected tr", trs)
        result = self.app.transform_list(trs)
        print(result)
        # TODO: check result??
        new_app = self.app.generate_code()
        new_app.compile()
        new_time = new_app.measure()
        print("optimized time:", new_time)
        # TODO: clone the app
        # TODO: repeat to the node selection again
        if depth > 2:
            return

    def roll(self, depth=0):
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_from_nodes()
        child = self.select_child()
        child.roll(depth+1)
