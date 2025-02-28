import random

from tadashi.apps import Polybench

# TODO: implement Upper Confidence Bound for sampling strategy

# UCT(node) = Q(node) + C * sqrt(ln(N(parent))/N(node))

#     Q(node): Average reward (win rate) of the node (exploitation).
#     N(parent): Number of visits to the parent node.
#     N(node): Number of visits to the node.
#     C: Exploration constant (balances exploration vs. exploitation).

# can start from C=1

class MCTSNode:
    def __init__(self, parent=None, app=None, action=None):
        self.parent = parent
        self.app = app
        self.action = action
        self.children = None
        self._number_of_visits = 0

    # def get_networkx_tree(self, graph=None, parent=None):
    #     # TODO: this is WIP
    #     if graph is None:
    #         graph = nx.Graph()
    #     graph.add_node(self)
    #     return graph

    def print(self, depth=0):
        if self._number_of_visits == 0:
            return
        print(f"{' '*depth}", end="")
        print(f"V:{self._number_of_visits}", self.action)
        if self.children is None:
            return
        for c in self.children:
            c.print(depth+1)

    def set_actions_from_nodes(self):
        nodes = self.app.scops[0].schedule_tree
        nodes_transformable = []
        for node in nodes:
            if node.available_transformations:
                nodes_transformable.append(node)
        # TODO: do this lazily to avoid expensive cloning through code generation
            self.children = [MCTSNode(self, self.app, node) for node in nodes_transformable]

    # TODO: replace this with UCT weighting
    # Neural scoring in the future
    def select_child(self):
        child = random.choice(self.children)
        return child

    def select_node(self, depth=0):
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_from_nodes()
        child = self.select_child()
        child.select_transformation(depth+1)

    def set_actions_transformations(self):
        self.children = [MCTSNode(self, action=tr) for tr in self.action.available_transformations]

    def select_transformation(self, depth):
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_transformations()
        child = self.select_child()
        child.select_params(depth+1)

    # OK let us do the following here
    # be tail-recursing list of params until it is empty
    # then do eval and continue back to the node selection
    def select_params(self, depth):
        self._number_of_visits += 1
        print("selecting params")
        params = self.parent.action.available_args(self.action)
        print(params)
        if depth > 2:
            return

if __name__ == "__main__":
    app = Polybench("linear-algebra/blas/gemm", "./examples/polybench/", compiler_options=["-D", "LARGE_DATASET"])
    root = MCTSNode(app=app, action="START")
    root.select_node()
    print("samples tree as follows:")
    root.print()