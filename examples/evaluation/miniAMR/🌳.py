from tadashi.mcts.optimize import optimize_app

from app import miniAMR

app = miniAMR(run_args=["--nx", "42", "--ny", "42", "--nz", "42"])

# print(f"{len(app.scops)}")
optimize_app(app,
             rollouts=10)
print("all done")
