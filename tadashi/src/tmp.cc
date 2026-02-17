#include <cassert>
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

static __isl_give isl_union_set_list *
_filters_from_cst_upa(__isl_take isl_union_pw_aff *upa) {
  isl_ctx *ctx = isl_union_pw_aff_get_ctx(upa);
  isl_pw_aff_list *pa_list = isl_union_pw_aff_get_pw_aff_list(upa);
  isl_size n_pa = isl_pw_aff_list_n_pw_aff(pa_list);
  isl_set_list *set_list = isl_set_list_alloc(ctx, n_pa);
  isl_pw_aff_list_foreach(pa_list, _add_pa_range, &set_list);
  isl_set_list_sort(set_list, _cmp, nullptr);
  isl_union_set_list *filters = isl_union_set_list_alloc(ctx, n_pa);
  isl_union_map *umap = isl_union_map_from_union_pw_aff(upa);
  for (isl_size i = 0; i < n_pa; i++) {
    isl_set *set = isl_set_list_get_at(set_list, i);
    isl_pw_multi_aff *pma = isl_pw_multi_aff_from_set(set);
    isl_union_map *preimage = isl_union_map_preimage_range_pw_multi_aff(
        isl_union_map_copy(umap), pma);
    isl_union_set *dmn = isl_union_map_domain(preimage);
    filters = isl_union_set_list_add(filters, dmn);
  };
  isl_union_map_free(umap);
  isl_set_list_free(set_list);
  isl_pw_aff_list_free(pa_list);
  return filters;
}

static __isl_give isl_schedule_node *
_build_schedule(__isl_take isl_schedule_node *node,
                __isl_keep isl_multi_union_pw_aff *mupa, int pos,
                unsigned int num_dims) {
  std::cout << "pos/num_dims: " << pos << "/" << num_dims << std::endl;
  if (pos >= num_dims)
    return node;
  isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, pos);
  std::cout << "UPA: " << isl_union_pw_aff_to_str(upa) << std::endl;

  if (isl_union_pw_aff_every_pw_aff(upa, _pw_aff_is_cst, (void *)1)) {
    isl_union_set_list *filters = _filters_from_cst_upa(upa);
    isl_size num_filters = isl_union_set_list_n_union_set(filters);
    assert(num_filters > 0);
    if (num_filters == 1) {
      isl_union_set_list_free(filters);
      return node;
    }
    node = isl_schedule_node_insert_sequence(node, filters);
    isl_size num_children = isl_schedule_node_n_children(node);
    for (isl_size i = 0; i < num_children; ++i) {
      node = isl_schedule_node_child(node, i);
      isl_multi_union_pw_aff *branch = isl_multi_union_pw_aff_intersect_domain(
          isl_multi_union_pw_aff_copy(mupa),
          isl_schedule_node_filter_get_filter(node));
      node = isl_schedule_node_first_child(node);
      node = _build_schedule(node, branch, pos + 1, num_dims);
      node = isl_schedule_node_parent(node);
      isl_multi_union_pw_aff_free(branch);
      node = isl_schedule_node_parent(node);
    }
  } else {
    node = isl_schedule_node_insert_partial_schedule(
        node, isl_multi_union_pw_aff_from_union_pw_aff(upa));
    node = isl_schedule_node_first_child(node);
    node = _build_schedule(node, mupa, pos + 1, num_dims);
    node = isl_schedule_node_parent(node);
  }

  // std::cout << "NODE: " << isl_schedule_node_to_str(node) << std::endl;
  return node;
}

isl_schedule *
build_schedule_from_umap(__isl_take isl_union_set *domain,
                         __isl_take isl_union_map *map) {
  isl_ctx *ctx = isl_union_set_get_ctx(domain);
  isl_schedule *schedule = isl_schedule_from_domain(domain);
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  schedule = isl_schedule_free(schedule);

  isl_multi_union_pw_aff *mupa = isl_multi_union_pw_aff_from_union_map(map);
  isl_size num_dims = isl_multi_union_pw_aff_dim(mupa, isl_dim_out);
  std::cout << "BEFORE ROOT: " << isl_schedule_node_to_str(root) << std::endl;
  root = isl_schedule_node_first_child(root);
  root = _build_schedule(root, mupa, 0, num_dims);
  std::cout << "AFTER ROOT: " << isl_schedule_node_to_str(root) << std::endl;
  isl_multi_union_pw_aff_free(mupa);

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
