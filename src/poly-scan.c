#include <isl/local_space.h>
#include <isl/space_type.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/constraint.h>
#include <isl/id.h>
#include <isl/set.h>
#include <isl/set_type.h>
#include <isl/space.h>

__isl_give isl_basic_set *build_bset0(__isl_keep isl_ctx *ctx,
                                      __isl_keep isl_id *N_id, //
                                      __isl_keep isl_id *i_id, //
                                      __isl_keep isl_id *j_id) {
  isl_space *space;
  isl_local_space *ls;
  isl_constraint *c;
  isl_basic_set *bset;
  const unsigned ndim = 2;

  space = isl_space_unit(ctx);
  space = isl_space_add_param_id(space, isl_id_copy(N_id));
  space = isl_space_add_dims(space, isl_dim_set, ndim);
  space = isl_space_set_dim_id(space, isl_dim_set, 0, isl_id_copy(i_id));
  space = isl_space_set_dim_id(space, isl_dim_set, 1, isl_id_copy(j_id));

  bset = isl_basic_set_universe(isl_space_copy(space));
  ls = isl_local_space_from_space(isl_space_copy(space));

  c = isl_constraint_alloc_inequality(isl_local_space_copy(ls));
  c = isl_constraint_set_coefficient_si(c, isl_dim_set, 0, -1);
  c = isl_constraint_set_coefficient_si(c, isl_dim_param, 0, 1);
  bset = isl_basic_set_add_constraint(bset, c);

  c = isl_constraint_alloc_inequality(isl_local_space_copy(ls));
  c = isl_constraint_set_constant_si(c, -1);
  c = isl_constraint_set_coefficient_si(c, isl_dim_set, 0, 1);
  bset = isl_basic_set_add_constraint(bset, c);

  c = isl_constraint_alloc_inequality(isl_local_space_copy(ls));
  c = isl_constraint_set_coefficient_si(c, isl_dim_set, 1, -1);
  c = isl_constraint_set_coefficient_si(c, isl_dim_param, 0, 1);
  bset = isl_basic_set_add_constraint(bset, c);

  c = isl_constraint_alloc_inequality(isl_local_space_copy(ls));
  c = isl_constraint_set_coefficient_si(c, isl_dim_set, 0, -1);
  c = isl_constraint_set_coefficient_si(c, isl_dim_set, 1, 1);
  bset = isl_basic_set_add_constraint(bset, c);

  isl_space_free(space);
  isl_local_space_free(ls);

  return bset;
}

__isl_give isl_basic_set *build_bset1(__isl_keep isl_ctx *ctx, //
                                      __isl_keep isl_id *N_id, //
                                      __isl_keep isl_id *M_id) {
  isl_space *space;
  isl_constraint *c;
  isl_multi_aff *ma;
  isl_val *v;
  isl_aff *var;
  isl_aff *cst;
  isl_basic_set *bset;
  space = isl_space_unit(ctx);
  space = isl_space_add_param_id(space, N_id);
  space = isl_space_add_param_id(space, M_id);
  space = isl_space_add_unnamed_tuple_ui(space, 2);
  ma = isl_multi_aff_identity_on_domain_space(isl_space_copy(space));
  ma = isl_multi_aff_set_dim_name(ma, isl_dim_in, 0, "i");
  ma = isl_multi_aff_set_dim_name(ma, isl_dim_in, 1, "j");
  var = isl_multi_aff_get_at(ma, 0);

  v = isl_val_int_from_si(ctx, 1);
  cst = isl_aff_val_on_domain_space(isl_space_copy(space), v);
  bset = isl_aff_ge_basic_set(isl_aff_copy(var), cst);

  cst = isl_aff_param_on_domain_space_id(isl_space_copy(space),
                                         isl_id_copy(M_id));
  bset = isl_basic_set_intersect(bset, isl_aff_le_basic_set(var, cst));

  var = isl_multi_aff_get_at(ma, 1);
  cst = isl_aff_param_on_domain_space_id(isl_space_copy(space),
                                         isl_id_copy(N_id));
  bset = isl_basic_set_intersect(
      bset, isl_aff_eq_basic_set(isl_aff_copy(var), isl_aff_copy(cst)));

  isl_aff_free(var);
  isl_aff_free(cst);
  isl_multi_aff_free(ma);
  isl_space_free(space);
  return bset;
}

int main(int argc, char *argv[]) {
  printf("Hello world!\n");
  isl_ctx *ctx = isl_ctx_alloc();

  isl_id *N_id = isl_id_alloc(ctx, "N", NULL);
  isl_id *M_id = isl_id_alloc(ctx, "M", NULL);
  isl_id *i_id = isl_id_alloc(ctx, "i", NULL);
  isl_id *j_id = isl_id_alloc(ctx, "j", NULL);

  // Spaces begin
  // params, set, map
  isl_space *spaces[] = {isl_space_alloc(ctx, 3, 2, 1),  // 0 0 1
                         isl_space_params_alloc(ctx, 3), // 1 1 0
                         isl_space_set_alloc(ctx, 3, 2), // 0 1 0
                         isl_space_unit(ctx)};           // 1 1 0
  const int num_spaces = sizeof(spaces) / sizeof(*spaces);
  for (int i = 0; i < num_spaces; ++i) {
    printf("params: %d, set: %d, map: %d\n", //
           isl_space_is_params(spaces[i]),
           isl_space_is_set(spaces[i]), //
           isl_space_is_map(spaces[i]));
    printf("%s\n", isl_space_to_str(spaces[i]));
  }
  for (int i = 0; i < num_spaces; ++i)
    isl_space_free(spaces[i]);
  // Spaces end

  isl_basic_set *bsets[3];
  isl_basic_set *bset;
  bsets[0] = build_bset0(ctx, N_id, i_id, j_id);
  bsets[1] = build_bset1(ctx, N_id, M_id);
  bsets[2] = isl_basic_set_read_from_str(
      ctx, "[N] -> { [i, j] : j = i and 0 < i <= N }");
  for (int i = 0; i < 3; i++)
    printf("bset: %s\n", isl_basic_set_to_str(bsets[i]));

  for (int first = 0; first < 2; first++) {
    for (int n = 0; n <= 2 - first; n++) {
      bset = isl_basic_set_project_out(isl_basic_set_copy(bsets[1]),
                                       isl_dim_set, first, n);
      printf("bset proj (first=%d, n=%d): %s\n", first, n,
             isl_basic_set_to_str(bset));
      isl_basic_set_free(bset);
    }
  }

  isl_basic_set *bset1, *bset2;
  bset1 = isl_basic_set_project_out( //
      isl_basic_set_copy(bsets[0]), isl_dim_set, 0, 1);
  printf("bset1: %s\n", isl_basic_set_to_str(bset1));
  bset2 = isl_basic_set_project_out( //
      isl_basic_set_copy(bsets[1]), isl_dim_set, 0, 1);
  bset1 = isl_basic_set_align_params(bset1, isl_basic_set_get_space(bset2));
  printf("bset1: %s\n", isl_basic_set_to_str(bset1));
  // @todo(vatai) add constraint N < M
  printf("bset2: %s\n", isl_basic_set_to_str(bset2));
  bset = isl_basic_set_intersect(isl_basic_set_copy(bset1),
                                 isl_basic_set_copy(bset2));
  printf("intersection: %s\n", isl_basic_set_to_str(bset));
  isl_basic_set_free(bset1);
  isl_basic_set_free(bset2);
  /* isl_basic_set_free(bset); */

  // Free stuff
  for (int i = 0; i < 3; i++)
    isl_basic_set_free(bsets[i]);

  isl_id_free(N_id);
  isl_id_free(M_id);
  isl_id_free(i_id);
  isl_id_free(j_id);
  isl_ctx_free(ctx);
  return 0;
}
