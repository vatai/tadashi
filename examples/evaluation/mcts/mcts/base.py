import math
import random

from colorama import Fore, Style

from mcts import config


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

    # TODO: make this config
    def select_child(self):
        return self.select_child_random()

    def select_child_random(self):
        child = random.choice(self.children)
        return child

    # TODO: add policy component
    def select_child_PUCT(self):
        """Implement Upper Confidence Bound sampling strategy"""
        # return random.choice(self.children)
        # TODO: consider softmax
        exploration_constant = 1
        best_score = -1
        best_child = self.children[0]
        for child in self.children:
            if child._number_of_visits == 0:
                return child
            else:
                # UCB
                # UCT(node) = Q(node) + C * sqrt(ln(N(parent))/N(node))
                # Q(node): Average reward (win rate) of the node (exploitation).
                # N(parent): Number of visits to the parent node.
                # N(node): Number of visits to the node.
                # C: Exploration constant (balances exploration vs. exploitation).
                # can start from C=1
                exploitation_term = child.speedup / child._number_of_visits
                # exploration_term = exploration_constant * math.sqrt(math.log(self._number_of_visits) / child._number_of_visits)
                # ucb_score = exploitation_term + exploration_term
                # PUCT
                # adding a component from policy
                policy_child = 1 / len(self.children)
                exploitation_term = policy_child * (
                    math.sqrt(self._number_of_visits) / (1 + child._number_of_visits)
                )
                ucb_score = exploitation_term + exploration_constant * exploitation_term
                if ucb_score > best_score:
                    best_score = ucb_score
                    best_child = child
        # print("SCORES:",scores)
        # child = random.choice(self.children)
        return best_child

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
            print("speedup :", self.speedup)
            print("source  :", self.app.source)

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
            if (
                self.parent
                and hasattr(self, "evaluate")
                and best.speedup == self.speedup
            ):
                return
            best.is_best = True
            self.best = best
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
            c.print(depth + 1)

    def print_best(self, depth=0):
        if self._number_of_visits == 0:
            return
        print(f"{' '*depth}", end="")
        print(f"V:{self._number_of_visits} S:{self.speedup:0.4f} |", self.action)
        if self.best:
            self.best.print_best(depth + 1)

    def update_stats(self, speedup, transforms, source):
        epsilon = 0.1
        if abs(speedup - 1) < epsilon:
            speedup = 1
            # print("QUIT ON ", speedup)
            # return

        if self.speedup is None or speedup > self.speedup:
            self.speedup = speedup
            if self.parent:
                self.parent.update_stats(speedup, transforms, source)
            else:
                self.logger.log(speedup, transforms, source)

    @staticmethod
    def filter_transformations(available_transformations):
        filtered_transformations = []
        if "whitelist_transformations" in config:
            for tr in available_transformations:
                if tr in config["whitelist_transformations"]:
                    filtered_transformations.append(tr)
            return filtered_transformations
        return available_transformations
