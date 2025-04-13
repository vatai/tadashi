import logging
from subprocess import TimeoutExpired

import tadashi.mcts.base
import tadashi.mcts.node_transformation
from colorama import Fore, Style
from tadashi.mcts import config

scop_idx = config["scop_idx"]
# This is a bit confusing, but the name implies that we are on a level where we are
# SELECTING node, maybe I should shift naming
class MCTSNode_Node(tadashi.mcts.base.MCTSNode):

    def set_actions_from_nodes(self):
        nodes = self.app.scops[scop_idx].schedule_tree
        nodes_transformable = []
        for i in range(len(nodes)):
            # print(i, nodes[i])
            if self.get_ISL_node_transformations(nodes[i]):
                nodes_transformable.append(i)
                # print("trans node", i)
                # print("\t", nodes[i], nodes[i].available_transformations)
        # print("transformable nodes:", len(nodes_transformable))
        # TODO: do this lazily to avoid expensive cloning through code generation
        self.children = [tadashi.mcts.node_transformation.MCTSNode_Transformation(parent=self,
                                                                                  app=self.app,
                                                                                  action=node) for node in nodes_transformable]
    def get_transform_chain(self):
        # print("GETING CHAIN from", self)
        # self.print()
        # print("-----")
        if self.parent.parent.parent.parent:
            # print(self.parent.parent.parent.parent)
            transforms = self.parent.parent.parent.get_transform_chain()
        else:
            transforms = []
        node = self.parent.parent.action
        tr = self.parent.action
        args = self.action
        transforms.append([node, tr, *args])
        return transforms

    def evaluate(self):
        self._number_of_visits += 1
        if self._number_of_visits > 4:
            return
        trs = self.get_transform_chain()
        print("selected transform:", trs)
        self.app.reset_scops()
        try:
            legal = self.app.scops[scop_idx].transform_list(trs)[0]
            print("transform legal: ", legal)
            if legal:
                config["cnt_evals"] += 1
                # print("try generate code")
                new_app = self.app.generate_code(ephemeral=False)
                # print("try compile")
                new_app.compile()
                new_time = new_app.measure(repeat=config["repeats"],
                                           timeout=config["timeout"])
                print("optimized time:", new_time)
                speedup = self.get_initial_time() / new_time
                # self.source = new_app.source
                self.update_stats(speedup, trs, new_app.source.name)
            else:
                speedup = -1
                self.update_stats(speedup, trs, "")
            print("speedup:", speedup)
        except TimeoutExpired:
            print("timed out")
            self.update_stats(-1, trs, "")
        except Exception as e:
            print(Fore.RED, end="")
            print("failed to transform with the following exception:")
            print(e)
            print(Style.RESET_ALL, end="")
        finally:
            self.app.reset_scops()


    def roll(self, depth=0):
        logging.info('selecting a node to transform')
        # print("replaying transforms up to current")
        if self.parent:
            self.app.reset_scops()
            trs = self.get_transform_chain()
            self.app.scops[scop_idx].transform_list(trs)
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_from_nodes()
        # print("selected node as ", child)
        if self.children:
            child = self.select_child()
            child.roll(depth+1)
        else:
            print("NO NODES TO CHOOSE FROM")
            self.update_stats(-1)
