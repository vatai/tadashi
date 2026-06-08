#!/bin/env python

import argparse
import os
from pathlib import Path
from shlex import quote

from tadashi.apps import Polybench

CONFIGS = [
    {
        "name": "pet",
        "translator": "Pet",
        "env": [],
    },
    {
        "name": "pet-fcc",
        "translator": "Pet",
        "env": ["export CC=fcc"],
    },
    {
        "name": "polly-llvm21",
        "translator": "Polly",
        "env": ["module load LLVM/llvmorg-21.1.0"],
    },
]


SUBMISSION_TEMPLATE = r"""#!/bin/bash
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_DIR=$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)
RESULT_ROOT="$SCRIPT_DIR/$(basename -- "${{0%.*}}")"
ENTRYPOINT="$REPO_DIR/examples/evaluation/mcts/mcts_polybench.py"

mkdir -p "$RESULT_ROOT"

pjsub \
  -o "$RESULT_ROOT/pjsub.%j.stdout" \
  -e "$RESULT_ROOT/pjsub.%j.stderr" \
  --spath "$RESULT_ROOT/pjsub.%j.stat" \
  -x RESULT_ROOT="$RESULT_ROOT" \
  -x ENTRYPOINT="$ENTRYPOINT" <<'PJSUB_EOF'
#!/bin/bash
#PJM -g ra000012
#PJM -x PJM_LLIO_GFSCACHE=/vol0004
#PJM -N {job_name}
#PJM -L rscgrp={resource_group}
#PJM -L elapse={elapse}
#PJM -L node=1
#PJM --mpi "max-proc-per-node=1"
# #PJM --llio localtmp-size=40Gi
#PJM -S
#PJM -j

set -e

export TMPDIR=/worktmp
export LD_PRELOAD=/usr/lib/FJSVtcs/ple/lib64/libpmix.so

{env}

MPIRUN=(
  mpirun -n 1
  -stdout-proc "$RESULT_ROOT/pjsub.$PJM_JOBID.out"
  -stderr-proc "$RESULT_ROOT/pjsub.$PJM_JOBID.err"
)

FLAGS=(
{flags}
--prefix="$RESULT_ROOT"
)

mkdir -p "$RESULT_ROOT"
"${{MPIRUN[@]}}" python -u "${{ENTRYPOINT}}" "${{FLAGS[@]}}"
PJSUB_EOF
"""

RUN_ALL_TEMPLATE = """#!/bin/bash
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

{submission}
"""


def get_args():
    parser = Polybench.args_parser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("jobs/polybench_mcts"),
        help="Directory where generated PJSub scripts are written.",
    )
    parser.add_argument(  # cfg3
        "--rollouts",
        type=int,
        default=100,
        help="Number of rolls.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Initial seed.",
    )
    parser.add_argument(
        "--elapse",
        type=str,
        default="21:00:00",
        help="PJSub wall-time limit for each generated job.",
    )
    return parser.parse_args()


def config_str(args):
    fields = [
        f"ro{args.rollouts}",
    ]
    return "-".join(fields)


def build_submission_script(args, config, benchmark, path):
    flags = [
        f"--translator={config['translator']}",
        f"--benchmark={benchmark}",
        f"--dataset={args.dataset}",
        f"--oflag={args.oflag}",
        "--allow-omp" if args.allow_omp else "--no-allow-omp",
        f"--rollouts={args.rollouts}",
        f"--seed={args.seed}",
    ]
    return SUBMISSION_TEMPLATE.format(
        job_name=f"MCTS_{config['name']}_{benchmark}",
        resource_group="small",
        elapse=args.elapse,
        env="\n".join(config["env"]),
        flags="\n".join(f"  {quote(f)}" for f in flags),
    )


def main():
    args = get_args()
    benchmarks = [Path(str(b)).name for b in Polybench.get_benchmarks()]
    run_all = []
    for config in CONFIGS:
        for benchmark in benchmarks:
            path = (
                args.output_dir
                / args.dataset
                / config_str(args)
                / config["name"]
                / f"{benchmark}-seed{args.seed}.sh"
            )
            relative_path = path.relative_to(args.output_dir / args.dataset)
            run_all.append('"$SCRIPT_DIR"/' + quote(str(relative_path)))
            path.parent.mkdir(parents=True, exist_ok=True)
            body = build_submission_script(args, config, benchmark, path)
            path.write_text(body)
            os.chmod(path, 0o755)

    run_all_path = args.output_dir / args.dataset / f"{config_str(args)}_launcher.sh"
    run_all_path.parent.mkdir(parents=True, exist_ok=True)
    run_all_path.write_text(RUN_ALL_TEMPLATE.format(submission="\n".join(run_all)))
    os.chmod(run_all_path, 0o755)

    print("configs:", ", ".join(config["name"] for config in CONFIGS))
    print("benchmarks:", len(benchmarks))
    print("jobs:", len(run_all))
    print("run all:", run_all_path)


if __name__ == "__main__":
    main()
