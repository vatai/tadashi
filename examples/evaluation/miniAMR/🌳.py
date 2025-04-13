from tadashi import TrEnum
from tadashi.mcts.optimize import optimize_app

from app import miniAMR

app = miniAMR(run_args=["--nx", "42", "--ny", "42", "--nz", "42"])

# print(f"{len(app.scops)}")

allowed_transformations = {
    TrEnum.TILE1D,
    TrEnum.TILE2D,
    TrEnum.TILE3D,
    TrEnum.INTERCHANGE,
    TrEnum.FULL_FUSE,
    TrEnum.FULL_SPLIT,
}

optimize_app(app,
             rollouts=10000,
             scop_idx=0,
             whitelist_transformations=allowed_transformations)
print("all done")
