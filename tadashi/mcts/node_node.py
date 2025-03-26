import tadashi.mcts.node_transformation
from colorama import Fore, Style
from tadashi import TrEnum

from .base import MCTSNode


# This is a bit confusing, but the name implies that we are on a level where we are
# SELECTING node, maybe I should shift naming
class MCTSNode_Node(MCTSNode):

    def set_actions_from_nodes(self):
        nodes = self.app.scops[0].schedule_tree
        nodes_transformable = []
        #from time import sleep
        #sleep(1)
        for i in range(len(nodes)):
            print(i, nodes[i])
            if nodes[i].available_transformations:
                nodes_transformable.append(i)
        # TODO: do this lazily to avoid expensive cloning through code generation
            self.children = [tadashi.mcts.node_transformation.MCTSNode_Transformation(parent=self,
                                                                                      app=self.app.generate_code(),
                                                                                      action=node) for node in nodes_transformable]
        # print("done")

    def evaluate(self):
        self._number_of_visits += 1
        # cloned_app = self.app.generate_code()
        default_scop = 0
        node = self.parent.parent.action
        tr = self.parent.action
        args = self.action
        trs = [[default_scop, node, tr, *args]]
        print("selected transform:", trs)
        # TODO: make a copy of the app to continue on it
        # TODO: make another brach
        # TODO: 1 where we do not apply, but keep growing list of 
        # app_backup = self.app.generate_code()
        print("!we are in app ", self.app)
        try:
            result = self.app.transform_list(trs)
            print("transform result: ", result)
            if result.legal:
                print("try generate code")
                new_app = self.app.generate_code(ephemeral=False)
                print("try compile")
                new_app.compile()
                new_time = new_app.measure()
                print("optimized time:", new_time)
                speedup = self.get_initial_time() / new_time
                self.source = new_app.source
            else:
                speedup = -1
            self.update_stats(speedup)
            print("speedup:", speedup)
        except Exception as e:
            print(Fore.RED, end="")
            print("failed to transform with the following exception:")
            print(e)
            print(Style.RESET_ALL, end="")
        # finally:
            # self.app = app_backup


    def roll(self, depth=0):
        print("### selecting a node to transform")
        self._number_of_visits += 1
        if self.children is None:
            self.set_actions_from_nodes()
        child = self.select_child()
        print("selected node as ", child)
        child.roll(depth+1)
