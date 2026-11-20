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

1. `[ ]` **Get a working `polycc`.** Build Pluto locally through `third_party/Dockerfile`, or use `third_party/opt/bin/polycc` on Fugaku compute nodes. Verify on `jacobi-2d.c`.
2. `[ ]` **Inventory Pluto's pragmas.** Generate `*.pluto.c` for the 29 convertible PolyBench benchmarks with `examples/evaluation/pluto/compile.sh`. List every distinct pragma form and clause, with the benchmarks that use it.
3. `[ ]` **Define and script the equality check.** Compile both sources with identical flags and compare the disassembly of the kernel function (`objdump -d`, symbol names stripped). Run it once on a pragma-free Pluto output (`polycc` without `--parallel`) to learn which non-pragma differences (bounds, iterator types, declarations) already break equality.
4. `[ ]` **Reproduce the schedules.** For `jacobi-1d`, `jacobi-2d`, `gemm`: derive the Tadashi transformation list from the `T(S…)` lines Pluto prints, apply it with `Polybench(...).scops[0].transform_list`, and confirm `app.legal`.
5. `[ ]` **Close the pragma gap.** *Needs explicit permission: new code.* Extend the existing mark mechanism so a mark can carry each pragma form from step 2, starting with the `private` clause, then the vectorisation pragmas. Touches `tadashi_set_parallel`, `after_mark`, `print_for`, the mark parser at `tadashi/src/ccscop.cc:867`, and `TrEnum`/`TransformInfo` if a new transformation is needed.
6. `[ ]` **Close the non-pragma gaps.** *Needs explicit permission: new code.* Only for the differences that step 3 proved to change the binary.
7. `[ ]` **Verify per benchmark.** Run the step 3 check on all 29. Tabulate: identical / differs, with the first differing construct. Pin identical ones as tests in the format of `tests/test_pluto_fig4.c` (*new files: needs explicit permission*).
8. `[ ]` **Record results** here, including constructs that cannot be matched.
