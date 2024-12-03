from pathlib import Path

import tadashi
from tadashi.apps import Polybench, Simple

test_op = [
    [
        [(0, 2), tadashi.TrEnum.SET_PARALLEL, []],
        [(0, 1), tadashi.TrEnum.SET_LOOP_OPT, [0, 3]],
        [(0, 1), tadashi.TrEnum.FULL_SHIFT_VAL, [-47]],
        [(0, 3), tadashi.TrEnum.PARTIAL_SHIFT_VAL, [0, 39]],
        [(0, 1), tadashi.TrEnum.PARTIAL_SHIFT_VAL, [0, 34]],
        [(0, 3), tadashi.TrEnum.PARTIAL_SHIFT_VAR, [0, -22, 0]],
        [(0, 3), tadashi.TrEnum.SET_PARALLEL, []],
    ]
]


app_maternity = Simple("examples/depnodep.c")
app_maternity.compile()
print(f"{app_maternity.scops[0].scop_idx=}")
print("  Measure:", min([app_maternity.measure() for _ in range(5)]))

app = app_maternity.generate_code()
print(f"{app.scops[0].scop_idx=}")

# scops = app.scops

op_set = test_op[0]
for op in op_set:
    print("\n ", op)
    x1, x2 = op[0]
    tr = op[1]
    args = op[2]

    print(f"{x1=}")
    print(f"{app.scops[0].scop_idx=}")
    scop = app.scops[x1]
    print(f"{scop.scop_idx=}")
    node = scop.schedule_tree[x2]
    print(f"{node=}")
    print(
        "  Is tranformation possible?     %s"
        % ("Yes" if tr in node.available_transformations else "No")
    )

    lu = node.available_args(tr)
    print("  Number of arguments:           %d" % len(lu))
    for i in range(len(lu)):
        print("    Expected values for argument %d:" % i, lu[i])

    print("  Arguments being used:     ", args)
    legal = node.transform(tr, *args)
    # if legal:
    #     node.transform(tr, *args)

    print("  Legal? [%s]" % ("Yes" if legal else "No"))

    if legal:
        app_tmp = app.generate_code()
        app_tmp.compile()
        print("  Measure:", min([app_tmp.measure() for _ in range(5)]))
