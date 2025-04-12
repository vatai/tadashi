from tadashi.mcts.optimize import optimize_app

from app import miniAMR

app = miniAMR(run_args=["--nx", "50", "--ny", "50", "--nz", "50"])

# print(f"{len(app.scops)}")
optimize_app(app,
             rollouts=10)
print("all done")
