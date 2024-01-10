import heapq
import tadashi_wrapper

class GameState:
    def __init__(self, position, score):
        self.position = position  
        self.score = score  

    def __lt__(self, other):
        return self.score < other.score

def get_possible_moves(current_state):
    
    return [current_state.position + 1, current_state.position + 2, current_state.position + 3, current_state.position + 4]

def perform_move(current_state, move):
    return move

def game_score(state):
    tadashi_wrapper.invoke_tadashi(state)
    return state

def beam_search(initial_state, max_depth, beam_width):
    initial_node = GameState(position=initial_state, score=0)
    
    candidates = [initial_node]
    
    for _ in range(max_depth):
        new_candidates = []
        for node in candidates:
            possible_moves = get_possible_moves(node)
            
            for move in possible_moves:
                new_state = perform_move(node, move)
                new_score = node.score + game_score(new_state)
                new_candidates.append(GameState(position=new_state, score=new_score))
        
        candidates = heapq.nlargest(beam_width, new_candidates)
    
    best_path = max(candidates, key=lambda x: x.score)
    return best_path

initial_game_state = 0 
max_search_depth = 5
beam_width = 3
best_path = beam_search(initial_game_state, max_search_depth, beam_width)
print("Best Path:", best_path)
