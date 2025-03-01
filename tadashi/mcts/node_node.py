import tadashi.mcts.node_transformation

from .base import MCTSNode


# This is a bit confusing, but the name implies that we are on a level where we are
# SELECTING node, maybe I should shift naming
class MCTSNode_Node(MCTSNode):

    def set_actions_from_nodes(self):
        nodes = self.app.scops[0].schedule_tree
        nodes_transformable = []
        for node in nodes:
            if node.available_transformations:
                nodes_transformable.append(node)
        # TODO: do this lazily to avoid expensive cloning through code generation
            self.children = [tadashi.mcts.node_transformation.MCTSNode_Transformation(self, self.app, node) for node in nodes_transformable]

    def evaluate(self, depth):
        print("measuring performance")
        self._number_of_visits += 1
        if depth > 2:
            return
        cloned_app = self.app.generate_code()
        # TODO: clone the app
        # TODO: repeat to the node selection again

    def roll(self, depth=0):
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_from_nodes()
        child = self.select_child()
        child.roll(depth+1)
