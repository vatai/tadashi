# Goal

Preserve iterator names from the original code.

Today `codegen()` names every generated loop iterator by index
(`_tadashi_0`, `_tadashi_1`, …, `tadashi/src/codegen.c:501-509`), so a
transformed `gemm` comes out as
`for(int _tadashi_0 = 0; _tadashi_0 < Ni; ...)` instead of
`for(int i = ...)`. The generated code is what users read, diff against
the input and hand to a compiler, so the synthetic names make transformed
output hard to relate back to the source.

The original names are available: pet stores them as the set-dim names of
each statement's iteration domain, and they survive every transformation
because the statement space is never renamed. For
`tests/test_interchange_1.c`:

```
domain:   [N] -> { S_0[i, j, k1] : ...; S_1[i, j, k2] : ... }
schedule: [N] -> L_0[{ S_0[i, j, k1] -> [(i)]; S_1[i, j, k2] -> [(i)] }]
```

# Specifications

## 1. Scope

Only the C code generator is affected: `codegen()` in
`tadashi/src/codegen.c`. It already receives both the freshly parsed
`pet_scop` and the transformed `isl_schedule`, so no signature,
`codegen.pxd` or Python-side change is needed.

`codegen()` is only reached from `Translator.generate_code()` →
`Translator._codegen_callback()` (`tadashi/translators.py:267`), i.e. the
**Pet** path. `Polly` emits bitcode via `opt`, never C, so it is
unaffected.

The change is unconditional (no flag): the fallback rules guarantee that
whenever a name cannot be derived safely, today's `_tadashi_N` name is
used.

## 2. Name source

The name of the loop generated for schedule depth `d` is derived from the
*names of the iteration-domain dimensions* of the statements scheduled at
that depth (`isl_space_get_dim_name(..., isl_dim_set, ...)` of the
statement space), i.e. the iterator names written in the original source.

Band labels (`L_0`, `L_0_tile2d_outer`, `Fused`, …, maintained by
`split_and_sel_labels()`, `tadashi/src/transformations.c:57`) are *not*
used as the name source: they are synthetic, lost by `FULL_FUSE`
("Fused") and empty for JSON-imported scops. Deriving names from the
schedule expression needs no bookkeeping and works uniformly.

## 3. Candidate collection

Traverse the schedule tree top-down, left-to-right
(`isl_schedule_foreach_schedule_node_top_down`). For a band node whose
schedule depth is `b` (`isl_schedule_node_get_schedule_depth`) and which
has `m` members (`isl_schedule_node_band_n_member`), member `k` describes
depth `d = b + k`. For each `isl_pw_aff` of that member (one per
statement space, iterated with `isl_union_pw_aff_foreach_pw_aff` on
member `k` of the band's `isl_multi_union_pw_aff`):

* compute the set of input dims the expression involves with
  `isl_pw_aff_involves_dims(pa, isl_dim_in, pos, 1)`;
* if **exactly one** input dim is involved and it has a name, that name
  is a *candidate* for depth `d`; otherwise the `pw_aff` yields no
  candidate.

For each depth `d`, the candidate coming from the statement that appears
**first in the source** wins (see decision D2), i.e. the one with the lowest
index in `scop->stmts`. Depths with no candidate get no name.

Note that `isl_union_pw_aff_foreach_pw_aff()` visits the expressions in the
order of isl's internal hash table, which has nothing to do with the source
order, so each expression's statement is looked up in `scop->stmts` (matching
on the tuple name of `isl_pw_aff_get_domain_space()`) to rank it. Taking
whatever isl happens to hand over first would make the generated names depend
on isl's hashing.

`isl_pw_aff_involves_dims()` sees through div definitions
(`isl_local_space_get_active`), so tiled expressions correctly report a
single dim. Measured member expressions on `tests/test_interchange_1.c`:

| transformation | member expression | involved dims |
|---|---|---|
| original / `INTERCHANGE` | `S_0[i,j,k1] -> [(i)]` | `i` |
| `TILE_2D 13 25` outer | `[(i - (i) mod 13)]` | `i` |
| `TILE_2D 13 25` inner | `[((i) mod 13)]` | `i` |
| `SCALE 3` | `[(3i)]` | `i` |
| `FULL_SHIFT_VAR` | `[(-2i)]` | `i` |
| skew / shift-by-var across dims | `[(i + j)]` | `i`, `j` |

## 4. Reserved names (safety)

A candidate must not collide with an identifier the generated code already
uses at that point: `print_for()` emits `for(int NAME = ...)`, so a
colliding name would shadow the original and silently change the program's
meaning. Such a candidate is not thrown away, it is disambiguated by §5.
The reserved set is built once per `codegen()` call from:

1. parameter names of `scop->context` (`isl_dim_param`);
2. names of arrays/scalars accessed by **surviving** statements: for each
   `scop->stmts[i]` whose space (`pet_stmt_get_space`) is present in
   `isl_schedule_get_domain(schedule)`, walk `stmt->body` with
   `pet_tree_foreach_access_expr()` and collect
   `pet_expr_access_get_id()` names;
3. names of functions called by surviving statements
   (`pet_tree_foreach_expr()` + `pet_expr_foreach_call_expr()` +
   `pet_expr_call_get_name()`);
4. the macro names isl may emit: `min`, `max`, `floord`.

Separately, a candidate that is not a valid C identifier
(`[A-Za-z_][A-Za-z0-9_]*`) is rejected outright and falls back to §6. This is
only reachable for JSON-imported scops, whose dim names come from a jscop file
rather than from a C parser. There is no table of C keywords: the names come
from a C parser, so a keyword can never be one of them.

Rule 2 deliberately ignores statements eliminated as dead code. This is
what makes the common PolyBench pattern keep its names:
`tests/test_gemm.c` declares `int i, j, k;` *outside* `#pragma scop`, and
pet models them as scalars in `scop->arrays`, but
`ccScop::_pet_eliminate_dead_code()` (`tadashi/src/ccscop.cc`) drops the
statements that assign them, so nothing in the emitted code reads them
and `for (int i = ...)` is safe *and* desirable. It would **not** be safe
if a surviving statement still read a variable of that name
(`for (int x = ...) A[x] = x;` with `x` an outer scalar), which is
exactly what rule 2 catches. Reserving all of `scop->arrays` instead would
be safe but useless — it would throw away the names in every PolyBench
kernel.

## 5. Uniqueness

`isl_ast_build_set_iterators()` takes one flat list indexed by schedule
depth, so a name used at depth `d1` would shadow itself if reused at a
nested depth `d2`. Names are therefore made unique across the whole list:
when the chosen base name is already taken (by an earlier depth or by the
reserved set), append `_1`, `_2`, … until it is free (see decision D3).
Example — `TILE_2D 13 25` on an `i`/`j` nest yields `i`, `j`, `i_1`,
`j_1` (tile loops first, then point loops).

The reserved set of §4 seeds the same "already taken" set, so a candidate
that would shadow something is disambiguated the same way:
`tests/test_iter_names_shadow.c` declares a `double i` in front of
`#pragma scop` and *reads* it inside the scop, so the statement using it
survives dead code elimination, `i` is reserved and the `i` loop comes out
as `i_1`.

## 6. Fallback

A depth with no candidate, or whose candidate is not a valid identifier,
keeps the current name `_tadashi_<d>` (`<d>` = depth, so fallback names
stay stable and unique). A candidate colliding with a reserved name is
*not* a fallback case: §5 turns it into `<name>_1`, which is both safe and
more informative than `_tadashi_<d>`.

## 7. Limitations (documented, not fixed)

* **One name per depth.** The iterator list is flat, so sibling subtrees
  at the same depth share a name. After `INTERCHANGE` on
  `tests/test_interchange_1.c`, depth 2 is the `k1` loop in one branch
  and the `k2` loop in the other; both print as `k1`. This is cosmetic:
  statement bodies are printed from `isl_ast_expr`s built for the actual
  loop, so the code stays correct. Per-branch naming would require nested
  `isl_ast_build_node_from_schedule()` calls and is out of scope.

  When two sibling nests are tiled differently the shared names become
  actively misleading. `tests/test_gemm.c` (`FULL_SPLIT`, then `TILE_2D` on
  the first nest and `TILE_3D` on the second) comes out as

  ```c
  for(int i = 0; i < Ni; i += 13)          /* nest 1: i tiles   */
    for(int j = 0; j < Nj; j += 25)
      for(int i_1 = ...)                   /* nest 1: i points  */
        for(int j_1 = ...)
          C[i + i_1][j + j_1] *= beta;
  for(int i = 0; i < Ni; i += 13)          /* nest 2: i tiles   */
    for(int j = 0; j < Nk; j += 25)        /*         k tiles!  */
      for(int i_1 = 0; i_1 < Nj; i_1 += 7) /*         j tiles!  */
        for(int j_1 = ...)                 /*         i points! */
  ```

  i.e. in the second nest `j` runs over `Nk` and `i_1` over `Nj`, because
  depths 0-3 were already named after the first nest. The names are still
  unique, so the code compiles and computes the same thing, but they no
  longer say anything about the loop. D2's "fall back to `_tadashi_N` on any
  disagreement" alternative would print `i`, `_tadashi_1`, …, `_tadashi_3`,
  `k`, `j` there instead.
* **A name says "derived from", not "equal to".** A tiled, scaled or
  shifted loop whose expression involves only `i` is still called `i` (or
  `i_1`) although its values are not `i`'s (see decision D1).
* isl may append its own `c<N>` names when it needs an extra dimension
  mid-generation (`isl_ast_build_insert_dim()` for strided domains);
  these are unaffected.

## 8. Open decisions

* **D1 — how much rewriting still keeps a name?** Chosen: *any* member
  expression involving exactly one original dim keeps that dim's name —
  this covers tiling, scaling and shifting, which is where readable
  output matters most. Alternatives: (a) only an exact identity
  `S[i,j] -> [i]` keeps the name (tiled/scaled loops fall back to
  `_tadashi_N`); (b) also name loops mixing several dims (skewing) after
  their outermost dim.
* **D2 — statements/branches disagreeing at one depth** (`k1` vs `k2`
  above). Chosen: the statement that comes first in the source wins.
  Alternatives: most frequent wins; or fall back to `_tadashi_N` on any
  disagreement (which would keep the flat list from ever attaching a
  misleading name to a sibling subtree, at the cost of losing the names of
  every depth two nests disagree on — see the `gemm` example in §7).
* **D3 — disambiguating suffix for repeated base names** (tile and point
  loop both from `i`). Chosen: `i`, `i_1`, `i_2`, … in depth order.
  Alternatives: reuse the band-label suffix (`i_tile2d_outer` /
  `i_tile2d_inner`, matching the existing label convention, but only
  available while labels survive), or a tile-aware `i_t` / `i`.

# Implementation

All in `tadashi/src/codegen.c`, as static helpers; no header change.

1. **Name set** — `struct name_set` with `name_set_has()` /
   `name_set_add()` / `name_set_free()`, used both for the reserved names
   and for keeping the names handed out unique.
2. **Reserved names** — `collect_reserved_names()`: the `min`/`max`/`floord`
   macros, the `isl_dim_param` names of `scop->context`, then, for each
   `scop->stmts[i]` whose tuple name appears in
   `isl_schedule_get_domain(schedule)` (matched by tuple name rather than by
   space equality), `pet_tree_foreach_access_expr()` with
   `_add_accessed_name()` and `pet_tree_foreach_expr()` with
   `_add_called_names()`.
3. **Candidate collection** — `_collect_candidates()`, an
   `isl_schedule_foreach_schedule_node_top_down` callback which, for each
   band member, runs `_candidate_from_pw_aff()` over
   `isl_multi_union_pw_aff_get_at()` with
   `isl_union_pw_aff_foreach_pw_aff()`. Each candidate carries the
   `scop->stmts` index of the statement it came from (`_stmt_rank()`) so the
   lowest one wins (§3).
4. **Assembly** — `_iterator_list()` replaces the `_tadashi_%zu` loop:
   `_iterator_name()` (candidate or `_tadashi_<d>`) → `_unique_name()` →
   `isl_id_alloc()`. `_schedule_num_iterators()` is unchanged.
5. Everything allocated is freed before `_iterator_list()` returns. This
   runs once per scop per `generate_code()` call; a valgrind run over
   `tests/test_tile3d.c`, `tests/test_gemm.c` and
   `tests/test_iter_names_shadow.c` reports no leak from it.

# Tests

`tests/test_ccscop.py:178` auto-discovers every `tests/test_*.c`; the
expected output is the `///` comment block at the top of the file. All 21
files embed `_tadashi_N`.

* **Regenerate** the `///` blocks of all 21 `tests/test_*.c` files. A
  throwaway script that replays `TestCcScop.check`'s transform+generate
  steps and rewrites the block is the practical route; the diffs must be
  reviewed, not blindly accepted.
* **New golden tests** (auto-discovered, just add the files), one rule
  each:
  * `tests/test_iter_names_interchange.c` — `row`/`col` preserved and
    swapped;
  * `tests/test_iter_names_tile.c` — `TILE_2D` gives `i`, `j`, `i_1`,
    `j_1` (D3);
  * `tests/test_iter_names_shadow.c` — a `double i` declared in front of
    the scop and read by a surviving statement makes the `i` loop come out
    as `i_1` (§4 + §5);
  * `tests/test_iter_names_fuse.c` — `FULL_FUSE` of a `p` and a `q` loop
    keeps `p`, the source-first one (D2).

  Each needs at least one transformation: `Pet._codegen_callback()`
  (`tadashi/translators.py:284`) copies a scop through unchanged when
  `ccscop.modified` is false, so a golden test without a
  `/// TRANSFORMATION:` line would just echo its own input.
* **Keep `tests/test_gemm.c`** as the regression for the
  `int i, j, k;`-outside-the-scop pattern: it must come out with
  `i`/`j`/`k`-derived names and must still compile and run.

# Verification

1. Build: `python setup.py build_ext -i` — clean, no new warnings.
2. `python -m unittest discover tests` — 75 tests, all green (5 skipped).
3. `TILE_1D 32` + `INTERCHANGE` on PolyBench `gemm` reads `i`, `i_1`, `j`,
   `k` and shadows none of `alpha`, `beta`, `A`, `B`, `C`, `ni`, `nj`,
   `nk`.
4. `Polybench.dump_arrays()` before and after `generate_code()` is
   byte-identical for `gemm`, `trmm`, `gesummv` and `jacobi-1d` with a
   `TILE_1D 13` applied — naming does not alter semantics.
   `tests/test_ccscop.py::test_transformation_list` and
   `::test_repeated_code_generation` cover compile + repeated codegen.
5. valgrind (`--leak-check=full`) over `tests/test_tile3d.c`,
   `tests/test_gemm.c` and `tests/test_iter_names_shadow.c` — no leak from
   the new code. Note that `scripts/check_mem.sh` itself is stale: it names
   `tests.py.test_ctadashi.*` tests that no longer exist.
