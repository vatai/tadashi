# Goal

Create a tool that will help LLMs generate code which is correct against a reference implementation.

# Specification

If pjsub is on the PATH, you are on the Fugaku supercomputer. You need to submit jobs to the compute nodes. Keep fugaku specific code in launch scripts. Python code should not have any fugaku related code in it. On Fugaku, basically everything has to be executed on compute nodes. You are running on compute node, which does not share /tmp with compute nodes.

The paper corresponding to the project is in the paper subfolder. Don't modify the paper unless explicitly asked.

Do not add new source files unless explicitly instructed to. Do not add new functions or make medium or major code changes, only fix things. Don't add checks except where you know for sure that something failed. Always find/show proof of some error happening before implementing unneeded checks to avoid them.

Stop before each git commit. Suggest a commit message andand wait for confirmation to proceed.

Pluto fails converting adi.c.

# Plan/Steps

Full diagnosis: `examples/evaluation/FAILURE-ANALYSIS.md`.

- [x] Figure out why some benchmarks failed.
      - Pluto sweep, 25/180 jobs: `PLUTO` not forwarded by `pluto/fsub_all.sh` (killed `adi`), and
        `elapse=30:00` in `pluto/fsub.sh` too short for cholesky/lu/ludcmp/seidel-2d/floyd-warshall and for
        the `heat-3d` fcc compile.
      - `adi` has a second, independent cause (job 51054036): Clan cannot parse the `(DATA_TYPE)` casts at
        `adi.c:81-83`, so `polycc` extracts no SCoP and `adi.pluto.c` can never be generated. `adi` is the
        only one of the 30 benchmarks with a cast inside its scop. Fixing the job scripts will not help it.
      - Correctness sweep: 91 `ng` (not just the 7 tracebacks). Partly real, partly checker bugs —
        `pet-fcc` silently re-tests `pet`, `Polly.legal()` never inspects the transformed schedule, only
        `gens[-1]` is replayed, and the `.dump` binaries race between the st and mt jobs.
- [x] Check if heat3d extreme speedup is correct.
      - It is not. The ~1000x is GP + `polly-llvm21` finding `scale 0` on the outer time band: runtime
        23.0 s -> 0.023 s, i.e. exactly 1/TSTEPS (TSTEPS=1000). `tadashi_scale` does not validate `val > 0`
        and `Polly.legal()` checks the pristine on-disk jscop, so nothing rejected it — and the checker
        stamped it `>>> OK <<<`.

Follow-ups:

- [x] Fix `Polly.legal()` to write the jscop files before checking.
      - Verified on Fugaku (job 51051250, `verify/legal_check.py`): jacobi-2d MINI + Polly, `scale 0` on the
        time band (scop 1, node 1) is now rejected (`legal() == False`) where the old code said `True`; the
        six other scale-0 sites (the dependence-free i/j bands) stay legal, so nothing is over-rejected.
      - Observation: `Scop.transform()` returned `True` (i.e. `ccScop::check_legality` accepted) for *every*
        `scale 0`, including the time band. So with the Polly translator the isl-side legality check does not
        catch `scale 0` either — only the `opt` check now does.

- [x] Re-run the Pluto sweep with the fixed scripts (2026-09-09, jobs 51055888-51056062).
      - 174/174 jobs complete with 3 of 3 runs each (29 benchmarks x {gcc,fcc,clang-21} x {st,mt}; `adi`
        dropped because Pluto cannot convert it). `elapse=6:00:00` was enough: slowest run is
        floyd-warshall/fcc/st at 942 s.
      - `polycc` needs only `/home/apps/oss/llvm-v15.0.3/init.sh` (for `libomp.so`/`libclang-cpp.so.15`);
        `third_party/opt/lib` on `LD_LIBRARY_PATH` is *not* needed — probe job 51055620 converted jacobi-2d
        byte-identically with and without it. The earlier claim in FAILURE-ANALYSIS.md was unproven and is
        now corrected.
      - The Pluto logs reach the report for the first time: job outputs are named `*.%j.out` (the `collect`
        glob), measurements are printed as `<binary>:::<rep>:::<seconds>`, and `parse_pluto_files` matches
        the whole executable name instead of `name_parts[-2]` (which parsed the compiler as `"st"`). All 344
        distinct executable names in the logs parse; every compiler is gcc/fcc/clang-21.
      - Observation: the June "fcc is 20x faster on the solvers" gap was an artefact. fcc reproduces to the
        digit (cholesky 23.36 s, lu 52.57 s, ludcmp 93.80 s) while gcc/clang, previously >1800 s, now finish
        in 12.7/13.2 s (cholesky) and 25.6/18.6 s (lu). What they were doing in June is unexplained.
      - Note: `collect_results.py` cannot be run on Fugaku (no numpy/pandas for the login node's python3,
        and `.venv` is aarch64-only); the parser fix was verified against every executable name in the logs
        with the stdlib `re` module instead.

- [ ] Check the re-run heat-3d searches (jobs 51052754 st, 51052755 mt) once they finish. Both are the
      `polly-llvm21` variant, EXTRALARGE, ps200-mg10-nt2-n170, launched with the fixed `Polly.legal()`:
      `ML4TADASHI/scripts/{st,mt}-evo/EXTRALARGE/ps200-mg10-nt2-n170/polly-llvm21/heat-3d-seed42/pjsub.<jobid>.out`.
      - Expected: no `scale 0` on the time band in the winners, and the ~1000x speedup gone (the old runs
        were `pjsub.49170147.out` st and the mt counterpart).
      - Then re-check whether the other five `>>> OK <<<` polly-llvm21 winners with a non-positive `scale`
        (gemm mt, gesummv mt, covariance st, syrk st, plus heat-3d) are also invalid — `scale 0` on a
        dependence-free band is legal, so they need the check sweep to classify.
