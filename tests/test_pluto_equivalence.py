"""Pin binary equality between Tadashi-generated code and Pluto.

Each entry replays the transform list recorded in PLAN.md and checks,
via examples/evaluation/pluto/compare_asm.sh, that the generated
source compiles to the same binary as the committed
`<benchmark>.pluto.nounroll.c` reference (`polycc --nounrolljam`;
for mvt this equals default polycc output).
"""

import shutil
import subprocess
import unittest
from pathlib import Path

from tadashi import TrEnum
from tadashi.apps import Polybench

REPO = Path(__file__).parent.parent
COMPARE_ASM = REPO / "examples" / "evaluation" / "pluto" / "compare_asm.sh"
REFERENCE = REPO / "examples" / "evaluation" / "pluto" / "reference"

TRANSFORMS = {
    "linear-algebra/blas/gemm": [
        [1, "LIMIT_PARAM", 0, 2000], [2, "LIMIT_PARAM", 1, 2600],
        [3, "LIMIT_PARAM", 2, 2300], [5, "FULL_SPLIT"],
        [6, "TILE_2D", 32, 32], [12, "TILE_3D", 32, 32, 32],
        [13, "INTERCHANGE"], [12, "SET_PARALLEL", 0], [6, "SET_PARALLEL", 0],
        [10, "SET_VECTOR"], [20, "SET_VECTOR"],
    ],
    "linear-algebra/kernels/mvt": [
        [1, "FULL_FUSE"], [2, "FULL_FUSE"], [1, "LIMIT_PARAM", 0, 4000],
        [2, "TILE_2D", 32, 32], [2, "SET_PARALLEL", 0],
    ],
    "linear-algebra/blas/syrk": [
        [1, "LIMIT_PARAM", 0, 2600], [2, "LIMIT_PARAM", 1, 2000],
        [4, "FULL_SPLIT"], [5, "TILE_2D", 32, 32], [12, "INTERCHANGE"],
        [11, "TILE_3D", 32, 32, 32], [11, "SET_PARALLEL", 0],
        [8, "SET_VECTOR"], [5, "SET_PARALLEL", 0],
    ],
    "linear-algebra/blas/syr2k": [
        [1, "LIMIT_PARAM", 0, 2600], [2, "LIMIT_PARAM", 1, 2000],
        [4, "FULL_SPLIT"], [5, "TILE_2D", 32, 32], [12, "INTERCHANGE"],
        [11, "TILE_3D", 32, 32, 32], [11, "SET_PARALLEL", 0],
        [8, "SET_VECTOR"], [5, "SET_PARALLEL", 0],
    ],
    "linear-algebra/blas/trmm": [
        [1, "LIMIT_PARAM", 0, 2000], [2, "LIMIT_PARAM", 1, 2600],
        [5, "FULL_SPLIT"], [4, "FULL_SPLIT"], [5, "INTERCHANGE"],
        [5, "TILE_3D", 32, 32, 32], [8, "INTERCHANGE"], [9, "INTERCHANGE"],
        [13, "TILE_2D", 32, 32], [16, "SET_VECTOR"], [13, "SET_GUARD"],
        [14, "SET_PARALLEL", 0], [10, "SET_VECTOR"], [5, "SET_GUARD"],
        [6, "SET_PARALLEL", 0],
    ],
    "linear-algebra/kernels/doitgen": [
        [1, "LIMIT_PARAM", 0, 250], [2, "LIMIT_PARAM", 1, 220],
        [3, "LIMIT_PARAM", 2, 270], [9, "FULL_SPLIT"], [15, "TILE_1D", 32],
        [11, "TILE_2D", 32, 32], [8, "TILE_1D", 32], [14, "INTERCHANGE"],
        [19, "SET_VECTOR"], [18, "SET_GUARD"], [19, "SET_PARALLEL", 0],
        [15, "SET_VECTOR"], [12, "SET_GUARD"], [13, "SET_PARALLEL", 0],
        [9, "SET_VECTOR"], [8, "SET_GUARD"], [9, "SET_PARALLEL", 0],
        [4, "SET_GUARD"],
    ],
    "linear-algebra/blas/gemver": [
        [3, "INTERCHANGE"], [1, "FUSE", 0, 1], [4, "FUSE", 0, 1],
        [14, "LIMIT_PARAM", 0, 4000], [11, "LIMIT_PARAM", 0, 4000],
        [3, "LIMIT_PARAM", 0, 4000], [17, "TILE_2D", 32, 32],
        [13, "TILE_1D", 32], [4, "TILE_2D", 32, 32], [6, "INTERCHANGE"],
        [20, "SET_GUARD"], [21, "SET_PARALLEL_PRIVATE", 0, 4],
        [16, "SET_VECTOR"], [15, "SET_GUARD"],
        [16, "SET_PARALLEL_PRIVATE", 0, 4], [7, "SET_VECTOR"],
        [4, "SET_GUARD"], [5, "SET_PARALLEL_PRIVATE", 0, 4],
    ],
    "linear-algebra/kernels/atax": [
        [7, "FULL_SPLIT"], [1, "REORDER", [2, 0, 1, 3]],
        [1, "LIMIT_PARAM", 0, 1800], [2, "LIMIT_PARAM", 1, 2200],
        [16, "INTERCHANGE"], [16, "TILE_2D", 32, 32], [18, "INTERCHANGE"],
        [19, "SET_VECTOR"], [16, "SET_GUARD_PARAM", 0],
        [17, "SET_PARALLEL_PRIVATE", 0, 3], [12, "TILE_2D", 32, 32],
        [12, "SET_GUARD_PARAM", 1], [13, "SET_PARALLEL_PRIVATE", 0, 3],
        [9, "TILE_1D", 32], [10, "SET_VECTOR"],
        [9, "SET_PARALLEL_PRIVATE", 0, 3], [6, "TILE_1D", 32],
        [7, "SET_VECTOR"], [6, "SET_PARALLEL_PRIVATE", 0, 3],
    ],
    "linear-algebra/kernels/bicg": [
        [12, "FULL_SPLIT"], [7, "FULL_SPLIT"], [1, "REORDER", [2, 0, 3, 1]],
        [1, "LIMIT_PARAM", 0, 2200], [2, "LIMIT_PARAM", 1, 1800],
        [16, "TILE_2D", 32, 32], [16, "SET_GUARD_PARAM", 0],
        [17, "SET_PARALLEL_PRIVATE", 0, 3], [12, "INTERCHANGE"],
        [12, "TILE_2D", 32, 32], [14, "INTERCHANGE"], [15, "SET_VECTOR"],
        [12, "SET_GUARD_PARAM", 1], [13, "SET_PARALLEL_PRIVATE", 0, 3],
        [9, "TILE_1D", 32], [10, "SET_VECTOR"],
        [9, "SET_PARALLEL_PRIVATE", 0, 3], [6, "TILE_1D", 32],
        [7, "SET_VECTOR"], [6, "SET_PARALLEL_PRIVATE", 0, 3],
    ],
    "linear-algebra/blas/gesummv": [
        [9, "FULL_SPLIT"], [2, "FULL_SPLIT"], [1, "REORDER", [2, 0, 3, 1, 4]],
        [1, "LIMIT_PARAM", 0, 2800], [19, "TILE_1D", 32], [20, "SET_VECTOR"],
        [19, "SET_PARALLEL_PRIVATE", 0, 3], [15, "TILE_2D", 32, 32],
        [15, "SET_PARALLEL_PRIVATE", 0, 3], [11, "TILE_2D", 32, 32],
        [11, "SET_PARALLEL_PRIVATE", 0, 3], [8, "TILE_1D", 32],
        [9, "SET_VECTOR"], [8, "SET_PARALLEL_PRIVATE", 0, 3],
        [5, "TILE_1D", 32], [6, "SET_VECTOR"],
        [5, "SET_PARALLEL_PRIVATE", 0, 3], [2, "SET_GUARD"],
    ],
    "datamining/covariance": [
        [4, "FULL_SPLIT"], [19, "FULL_SPLIT"], [18, "FUSE", 2, 3],
        [18, "FULL_SPLIT"], [1, "REORDER", [1, 2, 3, 4, 0, 5, 6]],
        [1, "LIMIT_PARAM", 0, 2600], [2, "LIMIT_PARAM", 1, 3000],
        [29, "TILE_2D", 32, 32], [32, "SET_VECTOR"],
        [29, "SET_PARALLEL_PRIVATE", 0, 6], [24, "TILE_3D", 32, 32, 32],
        [28, "INTERCHANGE"], [29, "SET_VECTOR"], [24, "SET_GUARD_PARAM", 1],
        [25, "SET_PARALLEL_PRIVATE", 0, 6], [20, "TILE_2D", 32, 32],
        [23, "SET_VECTOR"], [20, "SET_PARALLEL_PRIVATE", 0, 6],
        [16, "TILE_2D", 32, 32], [19, "SET_VECTOR"],
        [16, "SET_PARALLEL_PRIVATE", 0, 6], [13, "TILE_1D", 32],
        [14, "SET_VECTOR"], [13, "SET_PARALLEL_PRIVATE", 0, 6],
        [9, "TILE_2D", 32, 32], [11, "INTERCHANGE"], [12, "SET_VECTOR"],
        [9, "SET_GUARD_PARAM", 1], [10, "SET_PARALLEL_PRIVATE", 0, 6],
        [6, "TILE_1D", 32], [7, "SET_VECTOR"],
        [6, "SET_PARALLEL_PRIVATE", 0, 6],
    ],
}


def _reference(bench: str) -> Path:
    return REFERENCE / f"{Path(bench).name}.pluto.nounroll.c"


def _make_test(bench: str, transforms: list):
    def test(self):
        app = Polybench(
            bench, compiler_options=["-DEXTRALARGE_DATASET", "-O3", "-fopenmp"]
        )
        scop = app.scops[0]
        for node_idx, tr, *args in transforms:
            scop.transform_list([[node_idx, TrEnum[tr], *args]])
        self.assertTrue(scop.legal)
        tapp = app.generate_code(ensure_legality=True)
        result = subprocess.run(
            [str(COMPARE_ASM), str(_reference(bench)), str(tapp.source)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    return test


@unittest.skipUnless(
    shutil.which("gcc") and shutil.which("objdump"),
    "needs gcc and objdump for compare_asm.sh",
)
class TestPlutoEquivalence(unittest.TestCase):
    pass


for bench, transforms in TRANSFORMS.items():
    name = Path(bench).name.replace("-", "_")
    setattr(TestPlutoEquivalence, f"test_{name}", _make_test(bench, transforms))


if __name__ == "__main__":
    unittest.main()
