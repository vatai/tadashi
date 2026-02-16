#include <iostream>

#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/ctx.h>
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

static isl_stat
collect_set(__isl_take isl_set *set, void *user) {
  isl_set_list **list = (isl_set_list **)user;
  *list = isl_set_list_add(*list, set); /* takes ownership */
  return isl_stat_ok;
}

int
cmpx(isl_set *a, isl_set *b, void *u) {
  std::cout << "<<<<ISL_SET >>>>> " << isl_set_to_str(a) << std::endl;
  isl_val *va = isl_set_plain_get_val_if_fixed(a, isl_dim_set, 0);
  isl_val *vb = isl_set_plain_get_val_if_fixed(b, isl_dim_set, 0);
  int res;
  if (isl_val_lt(va, vb))
    res = -1;
  else if (isl_val_gt(va, vb))
    res = 1;
  else
    res = 0;
  isl_val_free(va);
  isl_val_free(vb);
  return res;
}

isl_stat
add_pa(isl_pw_aff *pa, void *user) {
  isl_pw_aff_list **list = (isl_pw_aff_list **)user;
  *list = isl_pw_aff_list_add(*list, pa);
  return isl_stat_ok;
}

isl_schedule *
build_schedule_from_umap(isl_union_set *domain, isl_union_map *umap) {
  isl_multi_union_pw_aff *mupa;
  isl_schedule *schedule;
  isl_schedule_node *root;
  isl_ctx *ctx = isl_union_set_get_ctx(domain);
  std::cout << "MAP: " << isl_union_map_to_str(umap) << std::endl;
  schedule = isl_schedule_from_domain(domain);
  mupa = isl_multi_union_pw_aff_from_union_map(umap);
  root = isl_schedule_get_root(schedule);
  schedule = isl_schedule_free(schedule);

  root = isl_schedule_node_first_child(root);
  isl_size dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_out);
  std::cout << "ROOT BEFORE: " << isl_schedule_node_to_str(root) << std::endl;
  for (int pos = dim - 1; pos >= 0; pos--) {
    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, pos);
    std::cout << "UPA: " << isl_union_pw_aff_to_str(upa) << std::endl;
    if (isl_union_pw_aff_every_pw_aff(upa, pw_aff_is_cst, NULL)) {
      isl_pw_aff_list *pa_list = isl_pw_aff_list_alloc(ctx, 1);
      isl_union_pw_aff_foreach_pw_aff(upa, add_pa, &pa_list);
      std::cout << "PA LIST " << isl_pw_aff_list_to_str(pa_list) << std::endl;
      isl_union_map *map = isl_union_map_from_union_pw_aff(upa);
      isl_union_set *steps = isl_union_map_range(isl_union_map_copy(map));
      std::cout << "STEPS: " << isl_union_set_to_str(steps) << std::endl;
      isl_union_set_list *filters = isl_union_set_list_from_union_set(steps);
      std::cout << "FILTERS: " << isl_union_set_list_to_str(filters)
                << std::endl;
      root = isl_schedule_node_insert_sequence(root, filters);
    } else {
      std::cout << "SKIPPPPP" << std::endl;
      root = isl_schedule_node_insert_partial_schedule(
          root, isl_multi_union_pw_aff_from_union_pw_aff(upa));
    }
    std::cout << "ROOT AFTER: " << isl_schedule_node_to_str(root) << std::endl;
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

  std::cout << "ROOT BEFORE: " << isl_schedule_node_to_str(root) << std::endl;
  std::cout << "DONxE!" << std::endl;
  return 0;
}
