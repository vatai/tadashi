# Failure analysis of the 2026-06-11 evaluation sweep

Originally diagnosis only. Fixes applied since are marked in [Part 3](#part-3--recommended-follow-ups) and
mirrored in `PLAN.md`; the Pluto sweep has been re-run (see [1a-fix](#1a-fix-the-re-run-sweep-2026-09-09-is-complete)).

Data analysed:

- `examples/evaluation/pluto/{st,mt}-pluto/` — Pluto measurement sweep, job ids `492063xx`, 2026-06-11 17:34–18:02
- `examples/evaluation/data/check/{poc,mcts,evo}/` — correctness replay sweep, 2026-06-11 10:54–17:01
- `examples/evaluation/{poc,mcts}/` and `../ML4TADASHI/scripts/{st,mt}-evo/` — the search logs those replay

## Part 1 — Why benchmarks failed

### 1a. Pluto sweep: 25 of 180 jobs incomplete

| benchmarks | cause |
| --- | --- |
| `adi` × {gcc,fcc,clang-21} × {st,mt} | `PLUTO` never reaches the job — *and* Pluto cannot convert `adi.c` |
| `heat-3d-fcc` st+mt | fcc compile killed at the 30 min elapse limit |
| `cholesky`, `lu`, `ludcmp` × {gcc,clang-21} × {st,mt} | elapse limit, 0 of 3 runs completed |
| `seidel-2d` st (all 3), `floyd-warshall` st (fcc, clang-21) | elapse limit, 1–2 of 3 runs |

**The `PLUTO` variable never reaches the job.** `pluto/fsub_all.sh:4` sets `PLUTO=${PLUTO:-polycc}` in the
submitting shell, but never exports it, and the `pjsub` call (`fsub_all.sh:20-25`) forwards only `file`, `NT`
and `CC`. Inside the job `fsub.sh:32` therefore reduces to

```sh
test -f "${file%.c}.pluto.c" || "$file"      # $PLUTO is empty
```

i.e. it tries to *execute the C source*:

```
.d0049206335: line 32: .../examples/polybench/stencils/adi/adi.c: Permission denied
gcc: error: .../adi.pluto.c: No such file or directory
```

Only `adi` was affected, because the other 29 `.pluto.c` files already existed on disk. They are generated
artefacts, never tracked (`.gitignore:26`), so a fresh clone would fail on all 30.

The `${PLUTO:-polycc}` fallback cannot work either: there is no `polycc` on `PATH` on Fugaku, and none
anywhere on the machine outside this repo. The built one is `third_party/opt/bin/polycc` (aarch64, so it only
runs on a compute node). Its wrapper hardcodes build-tree paths, so `third_party/build/pluto/` must stay in
place, and it needs an LLVM `init.sh` sourced for `libomp.so`/`libclang-cpp.so.15`, which `fsub.sh` did not
do. (`third_party/opt/lib` on `LD_LIBRARY_PATH` turned out *not* to be needed: `readelf -d` shows no
RPATH/RUNPATH and its only other NEEDED library, `libgmp.so.10`, is system-provided. Probe job `51055620`
converted `jacobi-2d` with and without that path, byte-identically.) The paths referenced in
`fsub_compile.sh:14` and `data/check/fsub_all.sh:4` (`$REPO_ROOT/deps/build/pluto-0.13.0/polycc`) do not
exist at all.

**Forwarding `PLUTO` will still not fix `adi`: Pluto cannot convert `adi.c`.** Verified on a compute node
(job `51054036`, log `verify/pluto-adi.51054036.out`, script `verify/pluto-adi/job.sh`):

```
$ third_party/opt/bin/polycc adi.c
[Clan] Error: syntax error at line 81, column 39.
Error extracting polyhedra from source file: 'adi.c'
```

Line 81 is the first statement inside `#pragma scop`, and column 39 is the end of the cast expression:

```c
  DX = SCALAR_VAL(1.0)/(DATA_TYPE)_PB_N;     /* adi.c:81, plus :82 and :83 */
```

Clan — Pluto's polyhedral extractor — does not parse the `(DATA_TYPE)` cast, so no SCoP is extracted and no
`adi.pluto.c` is ever produced. `adi` is the *only* benchmark of the 30 with a cast inside its scop region
(`grep`-checked over the whole polybench tree), which is consistent with the other 29 having converted fine.
Pet and Polly handle the same file, so this is a Pluto-frontend limitation, not a broken benchmark. It has to
be handled at the source level (rewrite the three casts, or pre-process the file for Pluto) or `adi` has to be
dropped from the Pluto comparison — no change to the job scripts can recover it.

**`elapse=30:00` is too short.** `fsub.sh:6` allows 30 minutes and `fsub.sh:38-40` runs the binary three times
with no per-run budget — there is no `timeout` or `ulimit -t` anywhere in the evaluation scripts, so the
job-level limit kills the loop mid-measurement. Single-run evidence from the logs: `seidel-2d` clang-21 st =
914 s, `floyd-warshall` fcc st = 947 s. For `cholesky`, `lu` and `ludcmp` under gcc/clang-21 the log stops
right after the binary name, so one run alone exceeded 30 minutes. `rscgrp=small` permits far more.

`heat-3d-fcc` is the same limit hitting the *compiler* rather than the benchmark:

```
Internal error: CPU time limit exceeded.
Compilation aborted.
fcc: Driver has abnormally ended due to SIGTERM.
```

**Side observation, since resolved.** The June logs suggested fcc was more than 20× faster than gcc/clang on
the solvers. The re-run (below) shows the opposite — the gcc/clang binaries were not slow, they were stuck:

| benchmark (st) | fcc, June | fcc, re-run | gcc / clang-21, June | gcc / clang-21, re-run |
| --- | --- | --- | --- | --- |
| cholesky | 23.4 s | 23.36 s | > 1800 s | 12.68 s / 13.16 s |
| lu | 52.6 s | 52.57 s | > 1800 s | 25.59 s / 18.61 s |
| ludcmp | 93.8 s | 93.80 s | > 1800 s | 398.38 s / 304.32 s |

The fcc numbers reproduce to the digit, so the measurement itself is stable; what the gcc/clang binaries were
doing for >30 min in June (they now finish in 13–400 s) is unexplained. 180 jobs compiling and running
concurrently in the same polybench tree over LLIO is the obvious suspect, but nothing in the logs proves it.

### 1a-fix. The re-run sweep (2026-09-09) is complete

Jobs `51055888`–`51056062`, 174 = 29 benchmarks × {gcc,fcc,clang-21} × {st,mt}, all with 3 of 3 runs
(`grep -c ':::'` = 3 in every log; 522 measurement lines total). What changed:

- `pluto/fsub_all.sh` forwards `-x PLUTO=$REPO_ROOT/third_party/opt/bin/polycc` and drops `adi` from the
  benchmark list (hence 174 jobs, not 180).
- `pluto/fsub.sh` raises `elapse` to `6:00:00`, sources the LLVM 15 init in a subshell around `polycc` (so it
  cannot shadow the LLVM 21 module used for the `clang-21` compile), and prints
  `<binary>:::<rep>:::<seconds>` — the format `parse_pluto_files` already expects. Slowest run in the new
  data: `floyd-warshall` fcc st at 942 s, so 30 min was indeed the binding limit.
- Job outputs are now named `*.%j.out`: `collect_results.py` globs `*.out`, so the old
  `pluto-<bm>-<cc>.<jobid>` logs were invisible to it regardless of their format. The 174 new logs were
  renamed accordingly; the June logs keep their names (the Reproduction section below refers to them).
- `parse_pluto_files` took the compiler from `name_parts[-2]`, which on the new
  `<bm>.pluto.<dataset>_O3.<cc>.<st|mt>.x` names yields `"st"`. It now matches the whole name with
  `EXECUTABLE_NAME` (`collect_results.py:20`); all 344 distinct executable names in the logs, old and new,
  parse, and every `compiler` value is one of gcc/fcc/clang-21.

Still open, and pipeline-wide rather than Pluto-specific: `fastest_by_benchmark`
(`collect_results.py:381-389`) groups on `(benchmark, compiler)`, so st and mt are folded into one minimum —
for every method, not just Pluto. See the reporting list in
[Part 2](#the-reporting-pipeline-amplifies-rather-than-catches-this).

### 1b. The correctness sweep is far worse than its 7 tracebacks suggest

The verdict lines (`>>> OK <<<` / `<<< ng`), not the tracebacks, are the signal:

| method | OK | ng | ng: pet | pet-fcc | polly-llvm21 |
| --- | --- | --- | --- | --- | --- |
| poc | 123 | 22 | 2 | 2 | 18 |
| mcts | 122 | 26 | 13 | 13 | 0 |
| evo | 104 | 43 | 11 | 6 | 26 |

91 mismatches, plus 5 × `ValueError: The App is not in a legal state` (`tadashi/apps.py:164`, all
polly-llvm21: deriche st/mt, floyd-warshall mt) and 2 infrastructure flakes (`gemver.dump` "Exec format
error", `bicg.dump` missing after `ld: final link failed: Stale file handle`).

Several defects in the checker itself make these verdicts unreliable **in both directions** — some "failures"
are checker bugs, and some `OK`s are meaningless:

- **`pet-fcc` is not testing fcc.** `check/fsub.sh` never sets `CC`, and the backend is derived from the
  directory name as `path.parent.parent.name.split("-")[0].capitalize()` (`check/poc.py:13`, `mcts.py:14`,
  `evo.py:14`), so `pet-fcc` → `Pet` → default `gcc`. The `pet` and `pet-fcc` replays are identical runs.
  mcts reporting exactly 13 `ng` in both columns, on the same benchmarks, confirms it.
- **`Polly.legal()` validates the wrong thing** — see [Part 2](#part-2--the-heat-3d-speedup-is-not-real). The
  polly-llvm21 column is not a legality test at all, which is also why the 5 `not in a legal state` errors
  actually mean "`opt` failed on the *original* SCoP", not "the replayed sequence is illegal".
- **Only the last logged entry is replayed.** `run_tr(*gens[-1])` (`check/poc.py:50`, `mcts.py:57`,
  `evo.py:57`). For heat-3d ST the mcts jsonl holds a single record with `transform=[]`, so
  `check/mcts/st-mtcs-heat-3d.49200276` prints `>>> OK <<< heat-3d []` three times — the fastest MCTS variant
  is never validated.
- **The `.dump` binaries race.** `App.output_binary` is `source.with_suffix("")` (`apps.py:149-152`), i.e.
  inside the polybench source tree, while `check/fsub_all.sh` submits the st and mt jobs for a benchmark
  concurrently. Both write `examples/polybench/.../gemver.dump`, which explains both infrastructure flakes.
- **A false `OK` is possible.** `App.compile` only *prints* a non-zero return code (`apps.py:225-232`), and
  `dump_arrays` ignores the exit status and returns only stderr (`apps.py:470-477`), so two crashed runs
  compare equal. Relatedly, the `pet-fcc` entry of `check/evo/st-evo-heat-3d.49200274` has no verdict line at
  all — that check died silently.

## Part 2 — The heat-3d speedup is not real

The "extreme" number is the GP (`evo`) result in the `polly-llvm21` variant:

| | baseline | best | reported speedup |
| --- | --- | --- | --- |
| st | 23.039963 s | 0.021540 s | ~1069× |
| mt | 23.006784 s | 0.022795 s | ~1012× |

from `../ML4TADASHI/scripts/{st,mt}-evo/EXTRALARGE/ps200-mg10-nt2-n170/polly-llvm21/heat-3d-seed42/`.

### Mechanism: `scale 0` collapses the time loop

The winning individuals contain `scale 0` applied to the outer (time) band. heat-3d at EXTRALARGE has
`TSTEPS 1000` (`examples/polybench/stencils/heat-3d/heat-3d.h:41`), and 23.0 / 0.023 ≈ 1000 = TSTEPS. The
transformation lists are recorded verbatim in the check output (`check/evo/{st,mt}-evo-heat-3d.*`):

```
>>> OK <<< heat-3d [[1, 1, 'full_shift_val', -7], [1, 1, 'scale', 0], [0, 2, 'tile_1d', 8], ...]   # mt
>>> OK <<< heat-3d [..., [1, 1, 'scale', 0]]                                                       # st
```

### Why nothing rejected it — two independent holes

1. **No argument validation.** `tadashi_scale` (`tadashi/src/transformations.c:468-475`) passes `val` straight
   to `isl_schedule_node_band_scale`, with no check that `val > 0`. There is no guard at the Python boundary
   either (`tadashi/__init__.py:22`, `tadashi/_tr_wrappers.py:41`).
2. **`Polly.legal()` never sees the transformed schedule.** It runs `opt -polly-import-jscop` against the
   jscop JSON files *on disk* (`tadashi/translators.py:456-469`). Those files still hold the pristine
   schedule at that moment: they are only rewritten by `_update_jscop` (`translators.py:509-524`), called
   later inside `generate_code`, whereas the legality gate runs first (`apps.py:162-164`). Codegen then passes
   `-disable-polly-legality` (`translators.py:479`). So in the polly-llvm21 variant nothing ever checks the
   transformed schedule.

   Contrast `Pet.legal()` (`translators.py:240`), which reads the per-SCoP `current_legal` flag recomputed on
   *every* transformation (`tadashi/scop.py:97` → `ccScop::check_legality`, `tadashi/src/ccscop.cc:860-886`).
   That is why `scale 0` never won in the pet variants — scaling by zero makes all dependence deltas zero,
   which `_check_legality` (`ccscop.cc:800-819`) rejects.

### Why the `>>> OK <<<` verdict did not catch it either

The checker replays through the same `Polly.legal()` hole, and additionally cannot distinguish a matching dump
from two failed ones (`apps.py:225-232`, `apps.py:470-477`).

**Open question:** whether the heat-3d polly-llvm21 `.dump` comparison genuinely matched, or silently compared
two empty outputs, has not been determined. See [Reproduction](#reproduction) for the check.

### The reporting pipeline amplifies rather than catches this

These affect every number in the paper's Fig. 5, not only heat-3d:

- **A crash is scored as 0 s, i.e. infinite speedup.** `Polybench.extract_runtime` (`apps.py:542-549`) returns
  `0.0` after printing "App probaly crashed", and `App.measure` takes `min(results)` (`apps.py:243`).
  `collect_results.py` filters `seconds > 0` for mcts (`:249`) and poc (`:295`), but `parse_evolution_log`
  (`:146-200`) does not.
- **Asymmetric sampling.** The baseline is a single sample (`poc/split-n-tile.py:118`, `measure()` defaults to
  `repeat=1`); the method time is the minimum over thousands of in-search single-shot measurements
  (`collect_results.py:186`, `:265-267`).
- **POC can never report a slowdown.** `parse_poc_stdout:288` includes the baseline in `min(measurements)`, so
  heat-3d's real 18× POC slowdown (fcc st: 15.67 s → 283.88 s) is reported as 1.000×.
- **st/mt and compilers are mixed.** `fastest_by_benchmark` (`collect_results.py:381-389`) groups on
  `(benchmark, compiler)` only, dropping the st/mt distinction; `build_abs_speedup`
  (`report_results.py:207-245`) divides the min-over-all-compilers original by the min-over-all-compilers
  method time. The heat-3d original varies 3.6× by compiler (gcc 56.4 s, fcc 15.6 s, clang 24.6 s).
- **The GP row uses someone else's baseline.** `data/main.py:250` takes
  `min(poc.otime, mcts.otime)` (24.66 s for heat-3d/clang/mt) instead of the GP's own 23.01 s.
- **Slowdowns are hidden and the outlier is clipped off the chart.** `main.py:167` `.clip(lower=1)` and
  `:189` `ylim(0.8, 320)`; the paper caption states this explicitly ("take the maximum of 1x and the actual
  speedup", `paper/main.tex:1019`), and the 1000× bar exceeds `ymax`.
- **The new Pluto logs were not parsed at all** — three separate reasons: the job outputs were not named
  `*.out` (the glob in `collect`), they printed bare numbers with no `:::`, and `parse_pluto_files` read the
  compiler as `name_parts[-2]`, i.e. `"st"` on `...EXTRALARGE_O3.clang-21.st.x`. Fixed; see
  [1a-fix](#1a-fix-the-re-run-sweep-2026-09-09-is-complete). `original_runs` still comes only from the older
  MT-only `pluto/results/*.out`, since the re-run sweep measures the Pluto binaries only.

## Part 3 — Recommended follow-ups

`[done]` items have been applied and verified; the rest are outstanding.

- Reject `scale` with `val <= 0` at the API boundary **and** `[done]` fix `Polly.legal()` to write the jscop
  files before checking, so the whole class of bug is caught generically instead of per-transformation.
- Treat all current `polly-llvm21` numbers — search results *and* `>>> OK <<<` verdicts — as invalid; re-run
  the searches and the check sweep once legality works, then diff against the old numbers.
- Make `App.compile` raise on a non-zero return code, and stop `extract_runtime` returning `0.0` for a crashed
  run.
- Set `CC` per variant in `check/fsub.sh` so `pet-fcc` actually tests fcc.
- Give each check job a private output directory so the `.dump` binaries stop racing.
- Replay every logged generation, not just `gens[-1]`.
- `[done]` In `pluto/fsub_all.sh`, forward `-x PLUTO=<abs path to third_party/opt/bin/polycc>`; raise the
  `fsub.sh` elapse limit to `6:00:00`. (`LD_LIBRARY_PATH` proved unnecessary; the LLVM 15 init is what
  `polycc` needs.)
- `[done]` `adi` is excluded from the Pluto comparison — the paper has to say so. Rewriting the three
  `(DATA_TYPE)` casts (`adi.c:81-83`) remains the alternative if a 30-benchmark Pluto column is wanted.
- `[done]` Make the Pluto logs reachable by the report: `*.%j.out` job outputs, `:::`-formatted measurement
  lines, and compiler extraction by full-name match in `parse_pluto_files`.

## Reproduction

All read-only.

```sh
cd examples/evaluation/pluto
# June sweep, incomplete jobs: 15 in st-pluto, 10 in mt-pluto (logs without .out)
for d in st-pluto mt-pluto; do
	for f in "$d"/*[0-9]; do
		n=$(grep -cE '^[0-9]+\.[0-9]+$' "$f")
		test "$n" -lt 3 && printf '%-45s runs=%s\n' "$(basename "$f")" "$n"
	done
done
# re-run sweep: 174 logs, 3 measurements each, nothing printed = all complete
ls st-pluto/*.out mt-pluto/*.out | wc -l
for f in st-pluto/*.out mt-pluto/*.out; do
	n=$(grep -cE ':::[0-9]+:::[0-9]+\.[0-9]+$' "$f")
	test "$n" -lt 3 && printf '%-45s runs=%s\n' "$(basename "$f")" "$n"
done
head -3 st-pluto/pluto-adi-gcc.49206335       # "adi.c: Permission denied"
tail -3 st-pluto/pluto-heat-3d-fcc.49206324   # "CPU time limit exceeded" / SIGTERM

# adi is the only benchmark with a cast inside its scop (what Clan chokes on)
for f in $(find ../../polybench -name '*.c' | grep -vE 'utilities|TMPFILE|INFIX|orig\.c|pluto\.c'); do
	awk '/#pragma scop/{s=1} s&&/\((DATA_TYPE|double|float|int)\)/{print FILENAME": "FNR": "$0} /#pragma endscop/{s=0}' "$f"
done

cd ../data/check
# verdict counts per method and per variant
for d in poc mcts evo; do
	echo "== $d"
	grep -ah '>>> OK <<<' "$d"/* | wc -l
	grep -ahB1 '<<< ng' "$d"/* | grep -oE '(pet-fcc|pet|polly-llvm21)/' | sort | uniq -c
done
grep -h "scale', 0" evo/*heat-3d*             # the scale 0 winners, stamped OK
```

The Pluto/`adi` failure needs a compute node (the `pluto` binary is aarch64), sources `llvm-v15.0.3/init.sh`
for `libomp.so` and puts `third_party/opt/lib` on `LD_LIBRARY_PATH`; `verify/pluto-adi/job.sh` does all three
and copies `adi.c`/`adi.h` into a scratch dir so the polybench tree is untouched:

```sh
pjsub -j -o "$PWD/verify/pluto-adi.%j.out" verify/pluto-adi/job.sh   # from the repo root
```

To settle the open question above, re-run one replay on a compute node and inspect both dumps:

```sh
cd examples/evaluation/data/check
pjsub -j -o /tmp/heat3d-recheck.%j \
	-x ENTRYPOINT=evo.py \
	-x BENCHMARK=heat-3d \
	-x ROOT="$PWD/../../../../ML4TADASHI/scripts/mt-evo" \
	fsub.sh
```

`>>> OK <<<` with two non-empty, identical dumps would mean `scale 0` is being dropped somewhere in the Polly
jscop round-trip. Empty dumps would confirm the false-`OK` path through `apps.py:225-232`.
