import argparse
from collections import defaultdict

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


def filter_tiles(trs):
    # for each si
    # ni in tile3d => ni, ni+1, ni+2 are covered by ni, 3d
    # ni in tile2d => ni, ni+1 are covered by ni, 2d
    # every ni should be covered only once and with 3d if possible or with the highest (=deepest) ni
    covers = defaultdict(list)
    for si, ni, tr in trs:
        tile_dim = int(str(tr)[5])
        for i in range(tile_dim):
            covers[si, ni + i].append((tr, ni))
    ret = []
    for (si, _), cover in covers.items():
        tr, ni = sorted(cover, reverse=True)[0]
        winner = [si, ni, tr]
        if winner not in ret:
            ret.append(winner)
    return ret


def add_params(trs, tile_size):
    ret = []
    for loc in trs:
        tr = loc[2]
        tile_dim = int(str(tr)[5])
        ret.append(loc + [tile_size] * tile_dim)
    return ret


def main(app, repeat, allow_omp):

    legal_trs = []

    r_splits = app.search_for("full_split")
    r_splits.reverse()
    extend_with_legal(app, legal_trs, r_splits)

    app.reset_scops()
    app.transform_list(legal_trs)
    print("FULL_SPLIT list legality:", app.legal)
    print(f"{legal_trs=}")

    tile3d = app.search_for("tile_3d")
    tile2d = app.search_for("tile_2d")
    tile_trs = filter_tiles(sorted(tile3d + tile2d, reverse=True))
    extend_with_legal(app, legal_trs, add_params(tile_trs, 32))
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
        compiler_options=[
            # "-DEXTRALARGE_DATASET",
            "-O3",
        ],
    )

    print(f"{app.user_compiler_options=}")
    print(f"{args.repeat=}")

    app.compile()

    print("Baseline measure: %f" % app.measure(repeat=args.repeat))
    tlist = main(app, args.repeat, args.allow_omp)
    measure(app, args.repeat, tlist)
