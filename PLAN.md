# Goal

Recreate the code generation capabilities of pluto.

# Specification

If pjsub is on the PATH, you are on the Fugaku supercomputer. You need to submit jobs to the compute nodes. Keep fugaku specific code in launch scripts. Python code should not have any fugaku related code in it. On Fugaku, basically everything has to be executed on compute nodes. You are running on login node, which does not share /tmp with compute nodes.

The paper corresponding to the project is in the paper subfolder. Don't modify the paper unless explicitly asked.

Do not add new source files unless explicitly instructed to. Do not add new functions or make medium or major code changes, only fix things. Don't add checks except where you know for sure that something failed. Always find/show proof of some error happening before implementing unneeded checks to avoid them.

Stop before each git commit. Suggest a commit message and wait for confirmation to proceed.

Pluto fails converting adi.c.

# Plan/Steps


Status legend: `[ ]` open, `[~]` in progress, `[x]` done. `adi` is out of scope.

Target: for every benchmark that Pluto (`polycc`) converts, Tadashi generates code that compiles to the same binary as Pluto's `*.pluto.c`. Known obstacle: Pluto emits pragmas which Tadashi cannot emit (Tadashi only emits `#pragma omp parallel for [num_threads(N)]`, via `tadashi_set_parallel` and `after_mark`/`print_for` in `tadashi/src/codegen.c`).

1. `[x]` **Get a working `polycc`.** Not on Fugaku. Built Pluto 0.13.0 release tarball at `deps/build/pluto-0.13.0` with system clang 12 (`./configure --with-clang-prefix=/usr`, `make -j`). Verified: converts `jacobi-2d.c`. Build Pluto locally through `third_party/Dockerfile`, or use `third_party/opt/bin/polycc` on Fugaku compute nodes. Verify on `jacobi-2d.c`.
2. `[x]` **Inventory Pluto's pragmas.** All 29 convertible benchmarks converted and compiled via `compile.sh` (adi fails in Clan: syntax error line 81, as expected). Only three pragma forms exist:
   - `#pragma ivdep` + `#pragma vector always` (always paired, 412×, in all 29 benchmarks, on vectorizable `lbv..ubv` innermost loops);
   - `#pragma omp parallel for private(lbv,ubv,<inner iterators>)` (68×, in 26 benchmarks; the `private` list is always `lbv,ubv` plus all loop iterators nested inside the parallel loop). `ludcmp`, `symm`, `durbin` have no omp pragma.
3. `[x]` **Define and script the equality check.** Script: `/tmp/claude-1827400009/-home-vatai-code-tadashi/b3978a68-f993-4d33-aaf2-efd1d8bdecc6/scratchpad/compare_asm.sh` (compiles both sources `-O3 -fopenmp -DEXTRALARGE_DATASET -DPOLYBENCH_TIME -DPOLYBENCH_USE_RESTRICT -c`, diffs `objdump -d` with addresses/symbols normalized; kept out of the repo pending permission for new files). Calibration on jacobi-2d: even `polycc --identity --notile --noparallel` output differs from the original at the binary level (133 diff lines; self-check orig-vs-orig is identical). The guilty constructs in Pluto's untransformed output: scop guard `if ((_PB_N >= 3) && (_PB_TSTEPS >= 1))`, iterator decls `int t1..t7; register int lbv, ubv;`, hoisted `lbv/ubv` bounds, rewritten index expressions (`A[t4][1+t6]`), and `ivdep`/`vector always` pragmas. Conclusion: binary equality requires Tadashi to reproduce Pluto's codegen idioms nearly token-for-token, not just the schedule.
4. `[x]` **Reproduce the schedules.** Done for all three; scripts in the session scratchpad (`gemm_repro.py`, `jacobi_repro.py`, `j2d_steps.py`), run inside a `tadashi-runtime` docker image (Ubuntu 24.04 + python3.12; the in-tree `.so`s need glibc 2.38, the Fedora 34 host has 2.33; repo bind-mounted at the same absolute path).
   - `gemm`: Pluto's exact default schedule `S1=(0,i/32,j/32,i,j)`, `S2=(1,i/32,j/32,k/32,i,k,j)` = `[[2,FULL_SPLIT],[3,TILE_2D,32,32],[9,TILE_3D,32,32,32],[10,INTERCHANGE]]`, legal=True, code generated and structure matches `gemm.pluto.c`.
   - `jacobi-1d` (Pluto `--nodiamond-tile`: `(t,2t+i)`, S2 +1): `[[2,FULL_FUSE],[2,FULL_SHIFT_VAR,0,2],[2,PARTIAL_SHIFT_VAL,1,1],[1,TILE_2D,32,32]]`, legal=True.
   - `jacobi-2d` (`(t,2t+i,2t+j)`, S2 +1,+1): `[[2,FULL_FUSE],[3,FULL_FUSE],[2,FULL_SHIFT_VAR,0,2],[2,PARTIAL_SHIFT_VAL,1,1],[3,FULL_SHIFT_VAR,0,2],[3,PARTIAL_SHIFT_VAL,1,1],[1,TILE_3D,32,32,32]]`, legal=True. (Shifting the other statement is correctly reported illegal.)
   - **Gap found:** Pluto's *default* stencil schedule is diamond tiling, `(2t-i, 2t+i)`, and its tile-level wavefront is `(t/32+(2t+i)/32, ...)`. Both shift an *outer* dim by an *inner* one (the matrix is not lower-triangular), which no current `TrEnum` transformation can express (`SCALE` is also unimplemented). Needs a new transformation (step 5/6 permission).
   - **Gap found:** besides pragmas, default `polycc` output applies 8×8 **unroll-jam with remainder loops** (e.g. `gemm.pluto.c`; done by the wrapper's orcc/vloog post-pass, not by the schedule). isl-based codegen cannot currently emit this; `jacobi-1d/2d` get no unroll-jam, so they are unaffected.
   - Baseline equality-check numbers (Tadashi vs `*.pluto.c`, normalized-disassembly diff lines): gemm 2251 (unroll-jam + pragmas), jacobi-1d 5627 and jacobi-2d 38445 (different schedule: Pluto defaults to diamond tiling + wavefront).
5. `[ ]` **Close the pragma gap.** *BLOCKED: waiting for explicit permission (new code).* *Needs explicit permission: new code.* Extend the existing mark mechanism so a mark can carry each pragma form from step 2, starting with the `private` clause, then the vectorisation pragmas. Touches `tadashi_set_parallel`, `after_mark`, `print_for`, the mark parser at `tadashi/src/ccscop.cc:867`, and `TrEnum`/`TransformInfo` if a new transformation is needed.
6. `[ ]` **Close the non-pragma gaps.** *Needs explicit permission: new code.* Only for the differences that step 3 proved to change the binary.
7. `[ ]` **Verify per benchmark.** Run the step 3 check on all 29. Tabulate: identical / differs, with the first differing construct. Pin identical ones as tests in the format of `tests/test_pluto_fig4.c` (*new files: needs explicit permission*).
8. `[ ]` **Record results** here, including constructs that cannot be matched.
