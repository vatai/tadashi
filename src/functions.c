/*
 * Test/debug code for set/map/point/constraint construction.
 *
 * Emil Vatai
 *
 */
#include <stdio.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/map.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

void param_space(isl_ctx *ctx) {
  unsigned int nparam = 3, n_in = 0, n_out = 0;
  isl_space *space = isl_space_alloc(ctx, nparam, n_in, n_out);
  isl_space *pspace = isl_space_params_alloc(ctx, nparam);
  isl_space *sspace = isl_space_set_alloc(ctx, nparam, n_out);
  isl_basic_set *set = isl_basic_set_empty(pspace);

  isl_space *uspace = isl_space_unit(ctx);
  uspace = isl_space_add_dims(uspace, isl_dim_param, 3);
  uspace = isl_space_set_dim_name(uspace, isl_dim_param, 2, "buz");

  printf("set %s\n", isl_basic_set_to_str(set));

  puts("");

  printf("space: %s\n", isl_space_to_str(space));
  printf("pspace: %s\n", isl_space_to_str(pspace));
  printf("sspace: %s\n", isl_space_to_str(sspace));
  printf("uspace: %s\n", isl_space_to_str(uspace));

  puts("");

  printf("is param space %d\n", isl_space_is_params(space));
  printf("is param pspace %d\n", isl_space_is_params(pspace));
  printf("is param pspace %d\n", isl_space_is_params(sspace));
  printf("is param uspace %d\n", isl_space_is_params(uspace));

  isl_basic_set_free(set);
  isl_space_free(space);
  isl_space_free(pspace);
  isl_space_free(sspace);
  isl_space_free(uspace);
}

void universe_and_empty_sets(isl_ctx *ctx) {
  isl_space *set_space = isl_space_unit(ctx);
  isl_space_add_dims(set_space, isl_dim_param, 1);
  isl_space_add_dims(set_space, isl_dim_out, 2); // isl_dim_out = isl_dim_set
  // isl_space_add_dims(space, isl_dim_in, 2); // all return `(null)`
  printf("set_space: %s\n", isl_space_to_str(set_space));

  isl_basic_set *bset = isl_basic_set_universe(isl_space_copy(set_space));
  printf("bset_universe: %s\n", isl_basic_set_to_str(bset));
  fflush(stdout);
  isl_basic_set_free(bset);

  isl_basic_set *bempty = isl_basic_set_empty(isl_space_copy(set_space));
  printf("bset_empty: %s\n", isl_basic_set_to_str(bempty));
  fflush(stdout);
  isl_basic_set_free(bempty);

  isl_set *set = isl_set_universe(isl_space_copy(set_space));
  printf("set_universe: %s\n", isl_set_to_str(set));
  fflush(stdout);
  isl_set_free(set);

  isl_set *empty = isl_set_empty(isl_space_copy(set_space));
  printf("set_empty: %s\n", isl_set_to_str(empty));
  fflush(stdout);
  isl_set_free(empty);

  isl_union_set *uempty = isl_union_set_empty(isl_space_copy(set_space));
  isl_union_set *uset = isl_union_set_universe(isl_union_set_copy(uempty));
  printf("uset_empty: %s\n", isl_union_set_to_str(uempty));
  fflush(stdout);
  printf("uset_universe: %s\n", isl_union_set_to_str(uset));
  fflush(stdout);
  isl_union_set_free(uset);
  isl_union_set_free(uempty);

  puts("");

  isl_map *lexmap = isl_map_lex_lt(isl_space_copy(set_space));
  printf("map_lex_lt: %s\n", isl_map_to_str(lexmap));
  fflush(stdout);
  isl_map_free(lexmap);

  puts("");

  isl_space *map_space = isl_space_unit(ctx);
  map_space = isl_space_add_dims(map_space, isl_dim_param, 1);
  map_space = isl_space_add_dims(map_space, isl_dim_in, 3);
  map_space = isl_space_add_dims(map_space, isl_dim_out, 2);
  printf("map_space: %s\n", isl_space_to_str(map_space));

  isl_basic_map *bmap = isl_basic_map_universe(isl_space_copy(map_space));
  printf("bmap_universe: %s\n", isl_basic_map_to_str(bmap));
  fflush(stdout);
  isl_basic_map_free(bmap);

  isl_basic_map *bempty_map = isl_basic_map_empty(isl_space_copy(map_space));
  printf("bempty_map_empty: %s\n", isl_basic_map_to_str(bempty_map));
  fflush(stdout);
  isl_basic_map_free(bempty_map);

  isl_map *pmap = isl_map_universe(isl_space_copy(map_space));
  printf("pmap_universe: %s\n", isl_map_to_str(pmap));
  fflush(stdout);
  isl_map_free(pmap);

  isl_map *pempty_map = isl_map_empty(isl_space_copy(map_space));
  printf("pempty_map_empty: %s\n", isl_map_to_str(pempty_map));
  fflush(stdout);
  isl_map_free(pempty_map);

  isl_union_map *uempty_map = isl_union_map_empty(isl_space_copy(map_space));
  printf("pempty_map_empty: %s\n", isl_union_map_to_str(uempty_map));
  fflush(stdout);
  isl_union_map *umap = isl_union_map_universe(uempty_map);
  printf("umap_universe: %s\n", isl_union_map_to_str(umap));
  fflush(stdout);
  isl_union_map_free(umap);
  isl_union_map_free(uempty_map);

  puts("");

  map_space = isl_space_add_dims(map_space, isl_dim_out, 1);
  printf("map_space: %s\n", isl_space_to_str(map_space));

  isl_map *pmap_id = isl_map_identity(isl_space_copy(map_space));
  printf("pmap_id: %s", isl_map_to_str(pmap_id));
  fflush(stdout);
  isl_map_free(pmap_id);

  isl_space_free(set_space);
  isl_space_free(map_space);
}

void points(isl_ctx *ctx) {
  isl_space *space = isl_space_unit(ctx);
  space = isl_space_add_dims(space, isl_dim_set, 2);

  isl_point *pt = isl_point_zero(space);

  printf("pt: %s\n", isl_point_to_str(pt));
  fflush(stdout);
  pt = isl_point_add_ui(pt, isl_dim_set, 1, 42);
  printf("pt: %s\n", isl_point_to_str(pt));
  fflush(stdout);
  pt = isl_point_add_ui(pt, isl_dim_set, 0, 10);
  printf("pt: %s\n", isl_point_to_str(pt));
  fflush(stdout);

  isl_point_free(pt);
  isl_space_free(space);
}

void aff_set(isl_ctx *ctx) {
  isl_space *space = isl_space_unit(ctx);
  space = isl_space_add_unnamed_tuple_ui(space, 2);

  printf("space: %s (is map %d)\n", isl_space_to_str(space),
         isl_space_is_set(space));

  isl_multi_aff *ma =
      isl_multi_aff_identity_on_domain_space(isl_space_copy(space));
  isl_aff *var = isl_multi_aff_get_at(ma, 0);
  isl_aff *cst = isl_aff_val_on_domain_space(isl_space_copy(space),
                                             isl_val_int_from_si(ctx, 42));
  isl_set *set = isl_aff_gt_set(isl_aff_copy(var), isl_aff_copy(cst));

  printf("ma: %s\n", isl_multi_aff_to_str(ma));
  printf("var: %s\n", isl_aff_to_str(var));
  printf("cst: %s\n", isl_aff_to_str(cst));
  printf("set: %s\n", isl_set_to_str(set));

  isl_set_free(set);
  isl_aff_free(cst);
  isl_aff_free(var);
  isl_multi_aff_free(ma);

  isl_multi_pw_aff *multi =
      isl_multi_pw_aff_identity_on_domain_space(isl_space_copy(space));
  printf("multi: %s\n", isl_multi_pw_aff_to_str(multi));
  isl_multi_pw_aff_free(multi);

  isl_space_free(space);
}

void pw_aff_map(isl_ctx *ctx) {
  isl_space *space = isl_space_unit(ctx);
  space = isl_space_add_unnamed_tuple_ui(space, 2);

  printf("space: %s (is map %d)\n", isl_space_to_str(space),
         isl_space_is_set(space));

  isl_multi_aff *ma =
      isl_multi_aff_identity_on_domain_space(isl_space_copy(space));
  /* isl_aff *var = isl_multi_aff_get_at(ma, 0); */
  /* isl_aff *cst = isl_aff_val_on_domain_space(isl_space_copy(space), */
  /*                                            isl_val_int_from_si(ctx, 42));
   */
  /* isl_set *set = isl_aff_gt_set(isl_aff_copy(var), isl_aff_copy(cst)); */

  /* TARGET: isl_pw_aff_gt_map(isl_pw_aff * pa1, isl_pw_aff * pa2) */

  /* printf("ma: %s\n", isl_multi_aff_to_str(ma)); */
  /* printf("var: %s\n", isl_aff_to_str(var)); */
  /* printf("cst: %s\n", isl_aff_to_str(cst)); */
  /* printf("set: %s\n", isl_set_to_str(set)); */

  /* isl_set_free(set); */
  /* isl_aff_free(cst); */
  /* isl_aff_free(var); */
  isl_multi_aff_free(ma);

  isl_multi_pw_aff *multi =
      isl_multi_pw_aff_identity_on_domain_space(isl_space_copy(space));
  printf("multi: %s\n", isl_multi_pw_aff_to_str(multi));
  isl_multi_pw_aff_free(multi);

  isl_space_free(space);
}

int main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  // param_space(ctx);
  // universe_and_empty_sets(ctx);
  // points(ctx);
  // aff_set(ctx);
  pw_aff_map(ctx);

  isl_ctx_free(ctx);
  printf("Done!\n");
}
