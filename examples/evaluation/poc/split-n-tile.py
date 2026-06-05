import argparse
from collections import defaultdict

from tadashi import TrEnum, translators
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


def add_params(trs, param):
    ret = []
    for loc in trs:
        tr = loc[2]
        if tr in [TrEnum.TILE_2D, TrEnum.TILE_3D]:
            rep = int(str(tr)[5])
        elif tr == TrEnum.SET_PARALLEL:
            rep = 1
        ret.append(loc + [param] * rep)
    return ret


def main(app, repeat, allow_omp, tile_size):

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
    extend_with_legal(app, legal_trs, add_params(tile_trs, tile_size))
    app.reset_scops()
    app.transform_list(legal_trs)
    print("TILE 2D and 3D list legality:", app.legal)

    if allow_omp:
        trs = app.search_for("set_parallel")  # [-2:]
        trs.reverse()
        extend_with_legal(app, legal_trs, add_params(trs, 0))
        app.reset_scops()
        app.transform_list(legal_trs)
        print("SET_PARALLEL list validity:", app.legal)

    return legal_trs


def measure(app, repeat, full_tr_list, tile_size):
    print("transformation_list=[")
    for t in full_tr_list:
        print(f"   {t},")
    print("]")

    print(f"Tiling with size {tile_size} ...")
    app.reset_scops()
    app.transform_list(full_tr_list)
    # print("Is this transformation list valid:", app.legal)
    tapp = app.generate_code(alt_infix=f"_tiled{tile_size}", ephemeral=False)
    tapp.compile()
    print(f"Tiling with size {tile_size}: {tapp.measure(repeat=repeat)}")

    print("[FINISHED APP]\n\n")


if __name__ == "__main__":
    parser = Polybench.args_parser()
    parser.add_argument("--repeat", type=int, default=1)
    parser.set_defaults(dataset="EXTRALARGE")
    parser.add_argument(
        "--allow-omp", action=argparse.BooleanOptionalAction, default=True
    )
    args = parser.parse_args()

    print("-----------------------------------------\n\n[STARTING NEW APP]")

    translator = getattr(translators, args.translator)
    print(args.benchmark)

    compiler_options = ([f"-{args.dataset}_DATASET", f"-O{args.oflag}"],)
    app = Polybench(
        args.benchmark,
        compiler_options=[f"-D{args.dataset}_DATASET", f"-O{args.oflag}"],
        translator=translator(),
    )

    print(f"{app.user_compiler_options=}")
    print(f"{args.repeat=}")

    app.compile()

    print(f"Baseline measure: {app.measure(repeat=args.repeat)}")
    tile_size = 20
    tlist = main(app, args.repeat, args.allow_omp, tile_size)
    measure(app, args.repeat, tlist, tile_size)
