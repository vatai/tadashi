#include <iostream>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/map.h>
#include <isl/multi.h>
#include <isl/point.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/space_type.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>
#include <ostream>

static isl_bool
_pw_aff_is_cst(__isl_keep isl_pw_aff *pa, void *user) {
  isl_bool target = (isl_bool)(user != 0);
  return (isl_bool)(isl_pw_aff_is_cst(pa) == target);
}

static isl_stat
_add_pa_range(isl_pw_aff *pa, void *user) {
  isl_set_list **set_list = (isl_set_list **)user;
  isl_map *map = isl_pw_aff_as_map(pa);
  *set_list = isl_set_list_add(*set_list, isl_map_range(map));
  return isl_stat_ok;
}

int
_cmp(struct isl_set *a, struct isl_set *b, void *user) {
  isl_val *va = isl_set_plain_get_val_if_fixed(a, isl_dim_set, 0);
  isl_val *vb = isl_set_plain_get_val_if_fixed(b, isl_dim_set, 0);
  isl_val *diff = isl_val_sub(va, vb);
  int rv = isl_val_sgn(diff);
  isl_val_free(diff);
  return rv;
}

static isl_schedule_node *
_build_rec(isl_schedule_node *node, isl_map_list *mlist, unsigned int cur_dim) {
  std::cout << "_build_rec: " << std::endl;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  isl_size num_maps = isl_map_list_n_map(mlist);
  isl_map_list *cur_proj = isl_map_list_alloc(ctx, num_maps);
  for (isl_size mi = 0; mi < num_maps; ++mi) {
    isl_map *map = isl_map_list_get_at(mlist, mi);
    isl_size ndim = isl_map_dim(map, isl_dim_out);
    isl_map *cur_map = isl_map_copy(map); // map needs freeing!
    cur_map = isl_map_project_out(cur_map, isl_dim_out, cur_dim + 1,
                                  ndim - cur_dim - 1);
    cur_proj = isl_map_list_add(cur_proj, cur_map);
  }
  std::cout << "cur_proj: " << isl_map_list_to_str(cur_proj) << std::endl;

  return node;
}

isl_schedule *
build_schedule_from_umap(__isl_take isl_union_set *domain,
                         __isl_take isl_union_map *map) {
  isl_ctx *ctx = isl_union_set_get_ctx(domain);
  isl_schedule *schedule = isl_schedule_from_domain(domain);
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  schedule = isl_schedule_free(schedule);
  root = isl_schedule_node_first_child(root);

  isl_map_list *mlist = isl_union_map_get_map_list(map);
  // isl_multi_union_pw_aff *mupa = isl_multi_union_pw_aff_from_union_map(map);
  // isl_union_pw_aff_list *upa_list = isl_multi_union_pw_aff_get_list(mupa);
  // isl_union_pw_aff *upa = isl_union_pw_aff_list_get_at(upa_list, 0);
  // std::cout << isl_union_pw_aff_to_str(upa) << std::endl;
  ///////////////
  // isl_union_pw_multi_aff *upma = isl_union_pw_multi_aff_from_union_map(map);
  // isl_size num_pma = isl_union_pw_multi_aff_n_pw_multi_aff(upma);
  // for (int i = 0; i < num_pma; ++i) {
  // }
  // std::cout << "dim: " << dim << "; "
  //           << "UPMA: " << isl_union_pw_multi_aff_to_str(upma) << std::endl;

  isl_union_map_free(map);
  // isl_union_pw_multi_aff_free(upma);

  root = _build_rec(root, mlist, 0);

  isl_map_list_free(mlist);

  schedule = isl_schedule_node_get_schedule(root);
  isl_schedule_node_free(root);
  return schedule;
}

int
main() {
  isl_ctx *ctx = isl_ctx_alloc();
  isl_union_set *domain = isl_union_set_read_from_str(
      ctx, "[p_0, p_1, p_2] -> { Stmt5[i0, i1, i2] : 0 <= i0 < p_0 and 0 <= i1 "
           "< p_2 and 0 <= i2 < p_1; Stmt2[i0, i1] : 0 <= i0 < p_0 and 0 <= i1 "
           "< p_1 }");
  isl_union_map *umap = isl_union_map_read_from_str(
      ctx, "[p_0, p_1, p_2] -> { Stmt2[i0, i1] -> [i0, 0, i1, 0]; Stmt5[i0, "
           "i1, i2] -> [i0, 1, i1, i2] }");
  isl_schedule *schedule = build_schedule_from_umap(domain, umap);
  isl_schedule_node *root;
  root = isl_schedule_get_root(schedule);

  std::cout << "========================================" << std::endl;
  std::cout << "========================================" << std::endl;
  std::cout << "ROOT BEFORE: " << isl_schedule_node_to_str(root) << std::endl;
  std::cout << "DONxE!" << std::endl;
  isl_schedule_free(schedule);
  isl_schedule_node_free(root);
  isl_ctx_free(ctx);
  return 0;
}
