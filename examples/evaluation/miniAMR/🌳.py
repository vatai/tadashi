from tadashi.mcts.optimize import optimize_app

print("oi")
from app import miniAMR

app = miniAMR()

print(f"{len(app.scops)}")
optimize_app(app,
             rollouts=10)
print("all done")
