import math
import random

class GameState:
    def __init__(self, position, is_terminal=False):
        self.position = position
        self.is_terminal = is_terminal

def get_possible_states(current_state):
    x, y = current_state.position
    possible_moves = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    return [GameState(position=move) for move in possible_moves]

def random_simulation(state):
    return random.uniform(0, 1)

def is_terminal(state):
    return state.is_terminal

class MonteCarloNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.score = 0
        
    def is_leaf(self):
        return not self.children 
    
    def is_terminal(self):
        return is_terminal(self.state)

def select(node):
    # Upper Confidence Bound (UCB)
    exploration_weight = 1.0
    while not node.is_terminal():
        if not node.children:
            expand(node)

        if all(child.visits > 0 for child in node.children):
            node = max(node.children, key=lambda c: c.score / c.visits + exploration_weight * math.sqrt(math.log(node.visits) / c.visits))
        else:
            node = random.choice(node.children)

    return node


def expand(node):
    
    possible_states = get_possible_states(node.state)
    for state in possible_states:
        new_node = MonteCarloNode(state, parent=node)
        node.children.append(new_node)
    return random.choice(node.children)

def simulate(node):
    return random_simulation(node.state)

def backpropagate(node, score):
    while node is not None:
        node.visits += 1
        node.score += score
        node = node.parent

def monte_carlo_tree_search(initial_state, max_iterations):
    root = MonteCarloNode(initial_state)

    for _ in range(max_iterations):
        selected_node = select(root)

        simulation_score = simulate(selected_node)

        backpropagate(selected_node, simulation_score)

    best_action_node = max(root.children, key=lambda c: c.visits)
    return best_action_node.state.position

def select_best_path(root):
    best_child = max(root.children, key=lambda c: c.visits) 
    best_path = [best_child.state] 
    
    while best_child.children:
        best_child = max(best_child.children, key=lambda c: c.visits) 
        best_path.append(best_child.state)

    return best_path

initial_game_state = GameState(position=(0, 0))
max_iterations = 1000
best_action = monte_carlo_tree_search(initial_game_state, max_iterations)
print("Best Action:", best_action)
