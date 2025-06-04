from tadashi import TrEnum

#from .optimize import opimize_app

# TODO: make this proper config
allowed_transformations = {
    TrEnum.TILE1D,
    TrEnum.TILE2D,
    TrEnum.TILE3D,
    TrEnum.INTERCHANGE,
    TrEnum.FULL_FUSE,
    TrEnum.FULL_SPLIT,
}


config = {"cnt_rollouts": 0,
          "repeats": 1,
          "rollouts": 1,
          "cnt_evals": 0,
          "scop_idx": 0,
          "max_depth": 2,
          #"whitelist_transformations": allowed_transformations
          }

