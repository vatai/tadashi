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
        "name": "polly-llvm19",
        "translator": "Polly",
        "env": ["source /home/apps/oss/llvm-v19.1.4/init.sh"],
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
ENTRYPOINT="$REPO_DIR/examples/polybench_evotadashi.py"

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
#PJM -L node={nodes}
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


def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate Fugaku PJSub scripts for Polybench EvoTADASHI runs."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("jobs/polybench_evotadashi"),
        help="Directory where generated PJSub scripts are written.",
    )
    parser.add_argument(  # before
        "--dataset",
        type=str,
        default="EXTRALARGE",
        help="Polybench dataset size passed to the runner.",
    )
    parser.add_argument(  # cfg1
        "--population-size",
        type=int,
        default=300,
        help="EvoTADASHI population size.",
    )
    parser.add_argument(  # cfg2
        "--max-gen",
        type=int,
        default=20,
        help="Maximum number of EvoTADASHI generations.",
    )
    parser.add_argument(  # cfg3
        "--n-trials",
        type=int,
        default=2,
        help="Number of evaluation trials per individual.",
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
    parser.add_argument(  # cfg4
        "--nodes",
        type=int,
        default=None,
        help="Allocated PJSub nodes. Defaults to population size + 1.",
    )
    parser.add_argument(
        "benchmarks",
        nargs="*",
        help="Optional Polybench benchmarks; filenames like cholesky are enough.",
    )
    return parser


def nodes(args):
    return args.nodes or args.population_size + 1


def config_str(args):
    fields = [
        f"ps{args.population_size}",
        f"mg{args.max_gen}",
        f"nt{args.n_trials}",
        f"n{nodes(args)}",
    ]
    return "-".join(fields)


def build_submission_script(args, config, benchmark, path):
    flags = [
        f"--translator={config['translator']}",
        f"--benchmark={benchmark}",
        f"--dataset={args.dataset}",
        f"--population-size={args.population_size}",
        f"--max-gen={args.max_gen}",
        f"--n-trials={args.n_trials}",
        f"--init_seed={args.seed}",
        "--use-mpi",
    ]
    return SUBMISSION_TEMPLATE.format(
        job_name=f"EvoT_{config['name']}_{benchmark}",
        resource_group="small",
        elapse=args.elapse,
        nodes=nodes(args),
        env="\n".join(config["env"]),
        flags="\n".join(f"  {quote(f)}" for f in flags),
        seed=args.seed,
    )


def main():
    args = get_parser().parse_args()
    bms = args.benchmarks if args.benchmarks else Polybench.get_benchmarks()
    benchmarks = [Path(str(b)).name for b in bms]
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
