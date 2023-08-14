#include <isl/local_space.h>
#include <isl/space_type.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/constraint.h>
#include <isl/id.h>
#include <isl/map.h>
#include <isl/schedule.h>
#include <isl/set.h>
#include <isl/set_type.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

void inspect_spaces(__isl_keep isl_ctx *ctx) {
  printf("--- inspect_spaces(ctx) ---\n\n");
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
    printf("%s\n\n", isl_space_to_str(spaces[i]));
  }
  for (int i = 0; i < num_spaces; ++i)
    isl_space_free(spaces[i]);
}

__isl_give isl_set *build_set0(__isl_keep isl_ctx *ctx,
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
  printf("x space: %s\n", isl_space_to_str(space));

  bset = isl_basic_set_universe(isl_space_copy(space));
  printf("stage0 bset: %s\n", isl_basic_set_to_str(bset));
  ls = isl_local_space_from_space(isl_space_copy(space));

  c = isl_constraint_alloc_inequality(isl_local_space_copy(ls));
  c = isl_constraint_set_coefficient_si(c, isl_dim_set, 0, -1);
  c = isl_constraint_set_coefficient_si(c, isl_dim_param, 0, 1);
  bset = isl_basic_set_add_constraint(bset, c);
  printf("stage1 bset: %s\n", isl_basic_set_to_str(bset));

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

  printf("final bset: %s\n", isl_basic_set_to_str(bset));

  isl_space_free(space);
  isl_local_space_free(ls);

  return isl_basic_set_to_set(bset);
}

__isl_give isl_set *build_set1(__isl_keep isl_ctx *ctx, //
                               __isl_keep isl_id *N_id, //
                               __isl_keep isl_id *M_id) {
  isl_space *space;
  isl_constraint *c;
  isl_multi_aff *ma;
  isl_val *v;
  isl_aff *var;
  isl_aff *cst;
  isl_basic_set *bset, *tmp_bset;
  space = isl_space_unit(ctx);
  space = isl_space_add_param_id(space, N_id);
  space = isl_space_add_param_id(space, M_id);
  space = isl_space_add_unnamed_tuple_ui(space, 2);
  space = isl_space_set_dim_name(space, isl_dim_set, 0, "i");
  space = isl_space_set_dim_name(space, isl_dim_set, 1, "j");
  // space: [N, M] -> { [i, j] }

  ma = isl_multi_aff_identity_on_domain_space(isl_space_copy(space));
  // ma: [N, M] -> { [i, j] -> [(i), (j)] }
  // identity/unit

  var = isl_multi_aff_get_at(ma, 0);
  // var: [N, M] -> { [i, j] -> [(i)] }
  v = isl_val_int_from_si(ctx, 1); // v: 1
  cst = isl_aff_val_on_domain_space(isl_space_copy(space), v);
  // cst: [N, M] -> { [i, j] -> [(1)] }
  bset = isl_aff_ge_basic_set(isl_aff_copy(var), cst);
  // bset: [N, M] -> { [i, j] : i > 0 } i >= 1

  cst = isl_aff_param_on_domain_space_id(isl_space_copy(space),
                                         isl_id_copy(M_id));
  // cst: [N, M] -> { [i, j] -> [(M)] }
  tmp_bset = isl_aff_le_basic_set(var, cst);
  // tmp_bset: [N, M] -> { [i, j] : i <= M }
  bset = isl_basic_set_intersect(bset, tmp_bset);
  // bset: [N, M] -> { [i, j] : 0 < i <= M }

  var = isl_multi_aff_get_at(ma, 1);
  // var: [N, M] -> { [i, j] -> [(j)] }
  cst = isl_aff_param_on_domain_space_id(isl_space_copy(space),
                                         isl_id_copy(N_id));
  // cst: [N, M] -> { [i, j] -> [(N)] }
  tmp_bset = isl_aff_eq_basic_set(var, cst);
  // tmp_bset: [N, M] -> { [i, j] : j = N }
  bset = isl_basic_set_intersect(bset, tmp_bset);
  // bset: [N, M] -> { [i, j] : j = N and 0 < i <= M }

  isl_multi_aff_free(ma); // this is causing the error
  isl_space_free(space);
  return isl_basic_set_to_set(bset);
}

void print_intersection(__isl_keep isl_set_list *slist,
                        __isl_keep isl_map_list *mlist, int idx0, int idx1) {
  isl_set *set;
  isl_map *map;
  set = isl_set_intersect(isl_set_list_get_at(slist, idx0),
                          isl_set_list_get_at(slist, idx1));
  printf("set intersection: %s\n", isl_set_to_str(set));
  isl_set_free(set);
  map = isl_map_intersect(isl_map_list_get_at(mlist, idx0),
                          isl_map_list_get_at(mlist, idx1));
  printf("map intersection: %s\n", isl_map_to_str(map));
  isl_map_free(map);
}

void project_and_intersect(__isl_keep isl_ctx *ctx) {
  printf("--- project_and_intersect(ctx) ---\n\n");
  isl_id *N_id = isl_id_alloc(ctx, "N", NULL);
  isl_id *M_id = isl_id_alloc(ctx, "M", NULL);
  isl_id *i_id = isl_id_alloc(ctx, "i", NULL);
  isl_id *j_id = isl_id_alloc(ctx, "j", NULL);

  isl_set_list *slist;
  isl_map_list *mlist;
  isl_set *set;
  isl_map *map;

  slist = isl_set_list_alloc(ctx, 3);

  set = build_set0(ctx, N_id, i_id, j_id);
  slist = isl_set_list_add(slist, set);

  set = build_set1(ctx, N_id, M_id);
  slist = isl_set_list_add(slist, set);

  set = isl_set_read_from_str(ctx, "[N] -> { [i, j] : j = i and 0 < i <= N} ");
  slist = isl_set_list_add(slist, set);

  isl_size size = isl_set_list_size(slist);
  mlist = isl_map_list_alloc(ctx, size);
  for (int i = 0; i < size; i++) {
    set = isl_set_list_get_at(slist, i);
    // set: [N] -> { [i, j] : 0 < i <= N and i <= j <= N }
    // set: [N, M] -> { [i, j = N] : 0 < i <= M }
    // set: [N] -> { [i, j = i] : 0 < i <= N }
    map = isl_set_project_onto_map(set, isl_dim_set, 0, 1);
    // map: [N] -> { [i, j] -> [i] : 0 < i <= N and i <= j <= N }
    // map: [N, M] -> { [i, j = N] -> [i] : 0 < i <= M }
    // map: [N] -> { [i, j = i] -> [i] : 0 < i <= N }
    mlist = isl_map_list_add(mlist, map);
  }

  print_intersection(slist, mlist, 0, 1);
  print_intersection(slist, mlist, 1, 2);
  print_intersection(slist, mlist, 2, 0);

  isl_set_list_free(slist);
  isl_map_list_free(mlist);
  isl_id_free(N_id);
  isl_id_free(M_id);
  isl_id_free(i_id);
  isl_id_free(j_id);
}

void schedule(__isl_keep isl_ctx *ctx) {
  printf("--- schedule(ctx) ---\n\n");
  isl_space *space;
  isl_multi_aff *ma;
  isl_aff *i_aff, *j_aff;
  isl_val *zero = isl_val_int_from_si(ctx, 0);
  isl_val *one = isl_val_int_from_si(ctx, 1);

  /* isl_id *N_id = isl_id_alloc(ctx, "N", NULL); */
  /* isl_id *M_id = isl_id_alloc(ctx, "M", NULL); */

  isl_schedule *schedule;
  isl_set *domain;
  isl_union_map *validity, *proximity;

  space = isl_space_params_alloc(ctx, 2);
  space = isl_space_add_unnamed_tuple_ui(space, 2);
  /* space = isl_space_add_param_id(space, N_id); */
  /* space = isl_space_add_param_id(space, M_id); */
  space = isl_space_set_dim_name(space, isl_dim_param, 0, "N");
  space = isl_space_set_dim_name(space, isl_dim_param, 1, "M");
  space = isl_space_set_dim_name(space, isl_dim_set, 0, "i");
  space = isl_space_set_dim_name(space, isl_dim_set, 1, "j");
  printf("space: %s\n", isl_space_to_str(space));
  // space: [N, M] -> { [i, j] }

  /* ma = isl_multi_aff_identity_on_domain_space(isl_space_copy(space)); */
  /* i_aff = isl_multi_aff_get_at(ma, 0); */
  /* j_aff = isl_multi_aff_get_at(ma, 1); */
  /* printf("ma: %s\n", isl_multi_aff_to_str(ma)); */
  /* printf("i_aff: %s\n", isl_aff_to_str(i_aff)); */
  /* printf("j_aff: %s\n", isl_aff_to_str(j_aff)); */
  /* domain = isl_aff_eq_basic_set(i_aff, cst); */
  /* domain = */
  /*     isl_set_read_from_str(ctx, "[N] -> { [i, j] : j = i and 0 < i <= N}");
   */
  char validity_str[] = "[N] -> { [i0] -> [o0] : 1 <= i0 <= N }";
  char proximity_str[] = "[N] -> { [i0] -> [o0] : 1 <= i0 <= N }";
  /* validity = isl_union_map_read_from_str(ctx, validity_str); */
  /* proximity = isl_union_map_read_from_str(ctx, proximity_str); */

  /* printf("domain: %s\n", isl_set_to_str(domain)); */
  /* printf("validity: %s\n", isl_union_map_to_str(validity)); */
  /* printf("proximity: %s\n", isl_union_map_to_str(proximity)); */

  /* schedule = isl_union_set_compute_schedule(domain, validity, proximity); */
  /* printf("schedule: %s\n", isl_schedule_to_str(schedule)); */

  /* isl_set_free(domain); */
  /* isl_union_map_free(validity); */
  /* isl_union_map_free(proximity); */

  isl_space_free(space);
  /* isl_id_free(N_id); */
  /* isl_id_free(M_id); */
  /* isl_multi_aff_free(ma); */
  /* isl_aff_free(i_aff); */
  /* isl_aff_free(j_aff); */
  isl_val_free(zero);
  isl_val_free(one);
}

int main(int argc, char *argv[]) {

  isl_ctx *ctx = isl_ctx_alloc();

  inspect_spaces(ctx);
  project_and_intersect(ctx);
  schedule(ctx);

  isl_ctx_free(ctx);

  printf("DONE!\n");
  return 0;
}
