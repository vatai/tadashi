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