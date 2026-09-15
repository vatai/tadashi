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
        return self.select_child_PUCT()

    def select_child_random(self):
        child = random.choice(self.children)
        return child

    # TODO: add policy component
    def select_child_PUCT(self):
        """Select a child using a uniform-prior PUCT score."""
        if not self.children:
            raise ValueError("cannot select a child from an empty node")

        exploration_constant = 1
        policy_child = 1 / len(self.children)
        best_child = self.children[0]
        best_score = -math.inf

        for child in self.children:
            if child._number_of_visits == 0:
                return child

            exploration_term = (
                exploration_constant
                * policy_child
                * (math.sqrt(self._number_of_visits) / (1 + child._number_of_visits))
            )
            puct_score = child.speedup + exploration_term
            if puct_score > best_score:
                best_score = puct_score
                best_child = child

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
