# Goal

Create a tool that will help LLMs generate code which is correct against a reference implementation.

# Specification

If pjsub is on the PATH, you are on the Fugaku supercomputer. You need to submit jobs to the compute nodes. Keep fugaku specific code in launch scripts. Python code should not have any fugaku related code in it. On Fugaku, basically everything has to be executed on compute nodes.

The paper corresponding to the project is in the paper subfolder. Don't modify the paper unless explicitly asked.

Do not add new source files unless explicitly instructed to. Do not add new functions or make medium or major code changes, only fix things. Don't add checks except where you know for sure that something failed. Always find/show proof of some error happening before implementing unneeded checks to avoid them.

Stop before each git commit. Suggest a commit message andand wait for confirmation to proceed.

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

- [x] Fix `Polly.legal()` to write the jscop files before checking.
      - Verified on Fugaku (job 51051250, `verify/legal_check.py`): jacobi-2d MINI + Polly, `scale 0` on the
        time band (scop 1, node 1) is now rejected (`legal() == False`) where the old code said `True`; the
        six other scale-0 sites (the dependence-free i/j bands) stay legal, so nothing is over-rejected.
      - Observation: `Scop.transform()` returned `True` (i.e. `ccScop::check_legality` accepted) for *every*
        `scale 0`, including the time band. So with the Polly translator the isl-side legality check does not
        catch `scale 0` either — only the `opt` check now does.

- [ ] Check the re-run heat-3d searches (jobs 51052754 st, 51052755 mt) once they finish. Both are the
      `polly-llvm21` variant, EXTRALARGE, ps200-mg10-nt2-n170, launched with the fixed `Polly.legal()`:
      `ML4TADASHI/scripts/{st,mt}-evo/EXTRALARGE/ps200-mg10-nt2-n170/polly-llvm21/heat-3d-seed42/pjsub.<jobid>.out`.
      - Expected: no `scale 0` on the time band in the winners, and the ~1000x speedup gone (the old runs
        were `pjsub.49170147.out` st and the mt counterpart).
      - Then re-check whether the other five `>>> OK <<<` polly-llvm21 winners with a non-positive `scale`
        (gemm mt, gesummv mt, covariance st, syrk st, plus heat-3d) are also invalid — `scale 0` on a
        dependence-free band is legal, so they need the check sweep to classify.
