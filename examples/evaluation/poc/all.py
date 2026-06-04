import argparse

from tadashi import TrEnum
from tadashi.apps import Polybench

apps_miniAMR = [
    "examples/evaluation/miniAMR/",
]


def extend_with_legal(app, base_trs: list[TrEnum], trs: list[TrEnum]) -> None:
    for tr in trs:
        app.reset_scops()
        app.transform_list(base_trs + [tr])
        if app.legal:
            base_trs.append(tr)


def main(app, repeat, allow_omp):

    # This list is being constructed

    r_splits = reversed(app.search_for("full_split"))
    print(f"{r_splits=}")
    legal_trs = []
    extend_with_legal(app, legal_trs, r_splits)

    app.reset_scops()
    app.transform_list(legal_trs)
    print("FULL_SPLIT list legality:", app.legal)
    print(f"{legal_trs=}")

    tile_size = 32
    tile3s = reversed(app.search_for("tile_3d"))
    for si, ni, tr in tile3s:
        if (si, ni - 1, tr) in tile3s:
            tile3s.pop(tile3s.index((si, ni - 1, tr)))
    trs3D = [[*tr, tile_size, tile_size, tile_size] for tr in tile3s]
    trs2 = app.search_for("tile_2d")
    trs2D = [[*tr, tile_size, tile_size] for tr in trs2[::-1]]
    trs3D.extend(trs2D)
    trs3D.sort()
    trs3D = trs3D[::-1]

    extend_with_legal(app, legal_trs, trs3D)
    app.reset_scops()
    app.transform_list(legal_trs)
    print("TILE 2D and 3D list legality:", app.legal)

    if allow_omp:
        trs = app.search_for("set_parallel")
        # trs = [[index, TrEnum.SET_PARALLEL, 0] for index in trs]
        trs = [[trs[0], TrEnum.SET_PARALLEL, 0]]
        trs = trs[::-1]
        extend_with_legal(app, legal_trs, trs)
        app.reset_scops()
        app.transform_list(legal_trs)
        print("SET_PARALLEL list validity:", app.legal)

    return legal_trs


def measure(app, repeat, full_tr_list):
    print("transformation_list=[")
    for t in full_tr_list:
        print("   %s," % str(t))
    print("]")

    for tile_size in [32]:
        print("Tiling with size %d ..." % tile_size)
        app.reset_scops()
        app.transform_list(full_tr_list)
        # print("Is this transformation list valid:", app.legal)
        tapp = app.generate_code(alt_infix="_tiled%d" % tile_size, ephemeral=False)
        tapp.compile()
        print("Tiling with size %d: %f" % (tile_size, tapp.measure(repeat=repeat)))

    print("[FINISHED APP]\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=str, default="jacobi-2d")
    parser.add_argument("--allow-omp", action=argparse.BooleanOptionalAction)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    print("-----------------------------------------\n\n[STARTING NEW APP]")

    print(args.benchmark)

    app = Polybench(
        args.benchmark,
        compiler_options=["-DEXTRALARGE_DATASET", "-O3"],
    )

    print(f"{app.user_compiler_options=}")
    print(f"{args.repeat=}")

    app.compile()

    print("Baseline measure: %f" % app.measure(repeat=args.repeat))
    tlist = main(app, args.repeat, args.allow_omp)
    measure(app, args.repeat, tlist)
