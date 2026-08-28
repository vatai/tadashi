# Goal

Create a tool that will help LLMs generate code which is correct against a reference implementation.

# Specification

If pjsub is on the PATH, you are on the Fugaku supercomputer. You need to submit jobs to the compute nodes.

The paper corresponding to the project is in the paper subfolder. Don't modify the paper unless explicitly asked.

# Plan/Steps

Full diagnosis: `examples/evaluation/FAILURE-ANALYSIS.md`.

- [x] Figure out why some benchmarks failed.
      - Pluto sweep, 25/180 jobs: `PLUTO` not forwarded by `pluto/fsub_all.sh` (killed `adi`), and
        `elapse=30:00` in `pluto/fsub.sh` too short for cholesky/lu/ludcmp/seidel-2d/floyd-warshall and for
        the `heat-3d` fcc compile.
      - Correctness sweep: 91 `ng` (not just the 7 tracebacks). Partly real, partly checker bugs —
        `pet-fcc` silently re-tests `pet`, `Polly.legal()` never inspects the transformed schedule, only
        `gens[-1]` is replayed, and the `.dump` binaries race between the st and mt jobs.
- [x] Check if heat3d extreme speedup is correct.
      - It is not. The ~1000x is GP + `polly-llvm21` finding `scale 0` on the outer time band: runtime
        23.0 s -> 0.023 s, i.e. exactly 1/TSTEPS (TSTEPS=1000). `tadashi_scale` does not validate `val > 0`
        and `Polly.legal()` checks the pristine on-disk jscop, so nothing rejected it — and the checker
        stamped it `>>> OK <<<`.

Follow-ups:

- [ ] Reject `scale` with `val <= 0` at the API boundary, and fix `Polly.legal()` to write the jscop files
      before checking.
- [ ] Treat all `polly-llvm21` results and verdicts as invalid; re-run searches and checks once legality
      works, then diff against the old numbers.
- [ ] Make `App.compile` raise on a non-zero return code; stop `extract_runtime` returning `0.0` on a crash.
- [ ] Set `CC` per variant in `check/fsub.sh` so `pet-fcc` actually tests fcc.
- [ ] Give each check job a private output dir so the `.dump` binaries stop racing.
- [ ] Replay every logged generation, not just `gens[-1]`.
- [ ] `pluto/fsub_all.sh`: forward `-x PLUTO=.../third_party/opt/bin/polycc` and `LD_LIBRARY_PATH`; raise
      `pluto/fsub.sh` elapse to `6:00:00`.
- [ ] Determine whether the heat-3d `polly-llvm21` dump comparison genuinely matched or compared two
      failures (`pjsub` recipe in `FAILURE-ANALYSIS.md`).
- [ ] Confirm the gcc/clang solver binaries (cholesky/lu/ludcmp, >1800 s vs fcc 23-94 s) are progressing and
      not hanging.
