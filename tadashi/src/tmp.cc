#include <iostream>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/map.h>
#include <isl/multi.h>
#include <isl/point.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>
#include <ostream>

static isl_bool
pw_aff_is_cst(__isl_keep isl_pw_aff *pa, void *_) {
  return isl_pw_aff_is_cst(pa);
}

isl_stat
add_filter(isl_pw_aff *pa, void *user) {
  isl_union_set_list **list = (isl_union_set_list **)user;
  isl_set *set = isl_pw_aff_domain(pa);
  *list = isl_union_set_list_add(*list, isl_union_set_from_set(set));
  return isl_stat_ok;
}

isl_schedule *
build_schedule_from_umap(isl_union_set *domain, isl_union_map *umap) {
  isl_multi_union_pw_aff *mupa;
  isl_schedule *schedule;
  isl_schedule_node *root;
  isl_ctx *ctx = isl_union_set_get_ctx(domain);
  schedule = isl_schedule_from_domain(domain);
  mupa = isl_multi_union_pw_aff_from_union_map(umap);
  root = isl_schedule_get_root(schedule);
  schedule = isl_schedule_free(schedule);

  root = isl_schedule_node_first_child(root);
  isl_size dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_out);
  for (int pos = dim - 1; pos >= 0; pos--) {
    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, pos);
    if (isl_union_pw_aff_every_pw_aff(upa, pw_aff_is_cst, NULL)) {
      isl_union_set_list *filters = isl_union_set_list_alloc(ctx, 1);
      isl_union_pw_aff_foreach_pw_aff(upa, add_filter, &filters);
      root = isl_schedule_node_insert_sequence(root, filters);
    } else {
      root = isl_schedule_node_insert_partial_schedule(
          root, isl_multi_union_pw_aff_from_union_pw_aff(upa));
    }
  }

  isl_multi_union_pw_aff_free(mupa);
  schedule = isl_schedule_node_get_schedule(root);
  isl_schedule_node_free(root);
  return schedule;
}

int
main() {
  isl_ctx *ctx = isl_ctx_alloc();
  isl_union_set *domain = isl_union_set_read_from_str(
      ctx, "[p_0, p_1, p_2] -> { Stmt6[i0, i1] : 0 <= i0 < p_0 and 0 <= i1 < "
           "p_2; Stmt10[i0, i1] : 0 <= i0 < p_2 and 0 <= i1 < p_1; Stmt2[i0, "
           "i1] : 0 <= i0 < p_0 and 0 <= i1 < p_1 }");
  isl_union_map *umap = isl_union_map_read_from_str(
      ctx, "[p_0, p_1, p_2] -> { Stmt10[i0, i1] -> [2, i0, i1]; Stmt6[i0, i1] "
           "-> [1, i0, i1]; Stmt2[i0, i1] -> [0, i0, i1] }");
  isl_schedule *schedule = build_schedule_from_umap(domain, umap);
  isl_schedule_node *root;
  root = isl_schedule_get_root(schedule);

  std::cout << "========================================" << std::endl;
  std::cout << "========================================" << std::endl;
  std::cout << "ROOT BEFORE: " << isl_schedule_node_to_str(root) << std::endl;
  std::cout << "DONxE!" << std::endl;
  return 0;
}
