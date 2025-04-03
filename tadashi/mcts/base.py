import random

from colorama import Fore, Style, init


class MCTSNode:
    def __init__(self, parent=None, app=None, action=None, initial_time=None):
        self.parent = parent
        self.app = app
        self.action = action
        self.children = None
        self._number_of_visits = 0
        self.initial_time = initial_time
        self.speedup = -1
        self.is_best = False
        self.best = None

    # TODO: implement Upper Confidence Bound for sampling strategy
    # UCT(node) = Q(node) + C * sqrt(ln(N(parent))/N(node))

    # Q(node): Average reward (win rate) of the node (exploitation).
    # N(parent): Number of visits to the parent node.
    # N(node): Number of visits to the node.
    # C: Exploration constant (balances exploration vs. exploitation).
    # can start from C=1

    # TODO: Neural scoring in the future
    def select_child(self):
        child = random.choice(self.children)
        return child

    def get_initial_time(self):
        if self.initial_time is not None:
            return self.initial_time
        return self.parent.get_initial_time()

    # def get_networkx_tree(self, graph=None, parent=None):
    #     # TODO: this is WIP
    #     if graph is None:
    #         graph = nx.Graph()
    #     graph.add_node(self)
    #     return graph

    def show_best_source(self):
        if self.best:
            self.best.show_best_source()
        else:
            print()
            print ("speedup :", self.speedup)
            print ("soruce  :", self.app.source)

    def set_best(self):
        self.is_best = True
        if self._number_of_visits == 0:
            return
        if self.children:
            best = max(self.children, key=lambda x: x.speedup)
            if best._number_of_visits == 0:
                return
            if best.speedup < self.speedup:
                return
            if self.parent and hasattr(self, "evaluate") and  best.speedup == self.speedup:
                return
            best.is_best = True
            self.best= best
            best.set_best()

    def print(self, depth=0):
        if self._number_of_visits == 0:
            return
        print(f"{' '*depth}", end="")
        if self.is_best:
            print(Fore.GREEN, end="")
        print(f"V:{self._number_of_visits} S:{self.speedup:0.4f} |", self.action)
        print(Style.RESET_ALL, end="")
        if self.children is None:
            return
        for c in self.children:
            c.print(depth+1)

    def print_best(self, depth=0):
        if self._number_of_visits == 0:
            return
        print(f"{' '*depth}", end="")
        print(f"V:{self._number_of_visits} S:{self.speedup:0.4f} |", self.action)
        if self.best:
            self.best.print_best(depth+1)

    def update_stats(self, speedup):
        if self.speedup is None or speedup > self.speedup:
            self.speedup = speedup
            if self.parent:
                self.parent.update_stats(speedup)
