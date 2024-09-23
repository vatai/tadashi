/** @file */
#include <assert.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/local_space.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include <pet.h>

#include "transformations.h"

isl_schedule_node *
limit_param_with_context(isl_schedule_node *node, int param_idx, int limit) {
  /**
   * @brief Insert a context node with `param_idx` to be less than
   * `limit`.
   */
  isl_id *param;
  isl_multi_union_pw_aff *mupa;
  isl_space *space;
  isl_multi_aff *ma;
  isl_aff *var, *val;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  param = isl_multi_union_pw_aff_get_dim_id(mupa, isl_dim_param, param_idx);
  mupa = isl_multi_union_pw_aff_free(mupa); // ???
  space = isl_space_unit(ctx);
  space = isl_space_add_dims(space, isl_dim_set, 1);
  space = isl_space_set_dim_id(space, isl_dim_set, 0, param);
  ma = isl_multi_aff_identity_on_domain_space(isl_space_copy(space));
  var = isl_multi_aff_get_at(ma, 0);
  ma = isl_multi_aff_free(ma);
  val = isl_aff_val_on_domain_space(space, isl_val_int_from_si(ctx, limit));
  isl_set *context = isl_aff_le_set(var, val);
  node = isl_schedule_node_insert_context(node, context);
  return isl_schedule_node_first_child(node);
}

isl_schedule_node *
tadashi_tile(isl_schedule_node *node, int tile_size) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  return isl_schedule_node_band_tile(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, tile_size))));
}

isl_schedule_node *
tadashi_interchange(isl_schedule_node *node) {
  isl_multi_union_pw_aff *mupa;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  node = isl_schedule_node_delete(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_insert_partial_schedule(node, mupa);
  return node;
}

__isl_give isl_union_set_list *
_fuse_get_filters(isl_schedule_node **node, __isl_take isl_union_set *filter,
                  int idx1, int idx2) {
  isl_union_set_list *filters;
  isl_ctx *ctx = isl_schedule_node_get_ctx(*node);
  isl_size size = isl_schedule_node_n_children(*node) - 1;
  filters = isl_union_set_list_alloc(ctx, size);
  for (int i = 0; i < size; i++) {
    isl_union_set *f;
    if (i >= idx2) {
      *node = isl_schedule_node_child(*node, i + 1);
      f = isl_schedule_node_filter_get_filter(*node);
      *node = isl_schedule_node_parent(*node);
    } else if (i == idx1) {
      f = filter;
    } else { // i < idx2
      *node = isl_schedule_node_child(*node, i);
      f = isl_schedule_node_filter_get_filter(*node);
      *node = isl_schedule_node_parent(*node);
    }
    filters = isl_union_set_list_insert(filters, i, f);
  }
  return filters;
}

__isl_give isl_schedule_node *
_fuse_insert_outer_shorter_sequence(__isl_take isl_schedule_node *node,
                                    int idx1, int idx2) {
  // Insert new sequence node with **one less filter nodes** above the
  // original sequence node. The inner, original sequence has the
  // original number of filters, with all but 2 being empty. Location
  // is at the new node.

  isl_union_set_list *filters;
  isl_union_set *filter;
  node = isl_schedule_node_child(node, idx1);
  filter = isl_schedule_node_filter_get_filter(node);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_child(node, idx2);
  filter =
      isl_union_set_union(filter, isl_schedule_node_filter_get_filter(node));
  node = isl_schedule_node_parent(node);
  filters = _fuse_get_filters(&node, filter, idx1, idx2);
  node = isl_schedule_node_insert_sequence(node, filters);
  return node;
}

struct _fuse_result_t {
  isl_union_set *filter;
  isl_union_set_list *filters;
  isl_multi_union_pw_aff *mupa;
};

__isl_give isl_schedule_node *
_fuse_get_filter_and_mupa(__isl_take isl_schedule_node *node, int idx,
                          struct _fuse_result_t *result,
                          isl_union_set_list **filters) {
  // Go down to first merged/non-empty filter and get the filter; Go
  // further down to the schedule node to get the schedule mupa and
  // restrict it to the filter. Go back up 2x (to the original node).
  isl_union_set *tmp;
  node = isl_schedule_node_child(node, idx);
  result->filter = isl_schedule_node_filter_get_filter(node);
  node = isl_schedule_node_first_child(node);
  result->mupa = isl_schedule_node_band_get_partial_schedule(node);
  result->mupa =
      isl_multi_union_pw_aff_reset_tuple_id(result->mupa, isl_dim_out);
  result->mupa =
      isl_multi_union_pw_aff_intersect_domain(result->mupa, result->filter);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);
  tmp = isl_union_set_copy(result->filter);
  isl_size pos = isl_union_set_list_size(*filters);
  *filters = isl_union_set_list_insert(*filters, pos, tmp);
  return node;
}

__isl_give isl_schedule_node *
tadashi_full_fuse(__isl_take isl_schedule_node *node) {
  // To merge all band node children of a sequence, take their partial
  // schedules, intersect them with the corresponding filters and take
  // the union.

  // Introduce a new band node on top of the sequence using If you
  // want, you can then also delete the original band nodes, but this
  // is not strictly required since they will mostly be ignored during
  // AST generation.  // printf("%s\n",
  // isl_schedule_node_to_str(node));
  enum isl_schedule_node_type node_type = isl_schedule_node_get_type(node);
  assert(node_type == isl_schedule_node_sequence ||
         node_type == isl_schedule_node_set);
  isl_size num_children = isl_schedule_node_n_children(node);
  node = isl_schedule_node_first_child(node);
  isl_multi_union_pw_aff *mupa = NULL;
  for (isl_size i = 0; i < num_children; i++) {
    assert(isl_schedule_node_get_type(node) == isl_schedule_node_filter);
    isl_union_set *filter;
    isl_multi_union_pw_aff *tmp;
    filter = isl_schedule_node_filter_get_filter(node);
    node = isl_schedule_node_first_child(node);
    assert(isl_schedule_node_get_type(node) == isl_schedule_node_band);
    tmp = isl_schedule_node_band_get_partial_schedule(node);
    tmp = isl_multi_union_pw_aff_intersect_domain(tmp, filter);
    tmp = isl_multi_union_pw_aff_reset_tuple_id(tmp, isl_dim_out);
    if (mupa == NULL) {
      mupa = tmp;
    } else {
      mupa = isl_multi_union_pw_aff_union_add(mupa, tmp);
    }
    node = isl_schedule_node_delete(node);
    node = isl_schedule_node_parent(node);
    if (i == num_children - 1)
      node = isl_schedule_node_parent(node);
    else
      node = isl_schedule_node_next_sibling(node);
  }
  mupa = isl_multi_union_pw_aff_set_tuple_name(mupa, isl_dim_out, "Fused");
  node = isl_schedule_node_insert_partial_schedule(node, mupa);
  return node;
}

__isl_give isl_schedule_node *
tadashi_fuse(__isl_take isl_schedule_node *node, int idx1, int idx2) {
  // If you don't want to fuse all the children of a sequence, you
  // first need to isolate those that you do want to fuse.  Take the
  // filters of the children of the original sequence node, collect
  // them in an isl_union_set_list, replacing the filters of the nodes
  // you want to fuse by a single (union) filter.  Insert a new
  // sequence node on top of the original sequence node.
  isl_union_set_list *filters;
  isl_multi_union_pw_aff *mupa;
  isl_union_set *tmp;
  struct _fuse_result_t result[2];
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);

  isl_size size = isl_schedule_node_n_children(node);
  assert(0 <= idx1 && idx1 < size);
  assert(0 <= idx2 && idx2 < size);
  node = _fuse_insert_outer_shorter_sequence(node, idx1, idx2);
  node = isl_schedule_node_child(node, idx1);
  node = isl_schedule_node_first_child(node);
  filters = isl_union_set_list_alloc(ctx, 2);
  node = _fuse_get_filter_and_mupa(node, idx1, &result[0], &filters);
  node = _fuse_get_filter_and_mupa(node, idx2, &result[1], &filters);
  mupa = isl_multi_union_pw_aff_union_add(result[0].mupa, result[1].mupa);
  node = isl_schedule_node_insert_sequence(node, filters);
  node = isl_schedule_node_insert_partial_schedule(node, mupa);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);
  return node;
}

isl_schedule_node *
tadashi_scale(isl_schedule_node *node, long scale) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  node = isl_schedule_node_band_scale(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, scale))));
  return node;
}

static __isl_give isl_schedule_node *
_tadashi_shift(__isl_take isl_schedule_node *node,
               __isl_give isl_pw_aff *(*fn)(__isl_keep isl_set_list *sets,
                                            isl_size set_loop_idx, int pa_idx,
                                            long coeff, long value),
               int pa_idx, long coeff, long value) {
  isl_multi_union_pw_aff *mupa;
  isl_union_pw_aff *upa;
  isl_union_set *upa_domain;
  isl_set_list *pa_domains;
  isl_id *id;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  // assert(isl_multi_union_pw_aff_dim(mupa, isl_dim_out) == 1);
  id = isl_multi_union_pw_aff_get_tuple_id(mupa, isl_dim_out);
  upa = isl_multi_union_pw_aff_get_at(mupa, 0);
  mupa = isl_multi_union_pw_aff_free(mupa);
  upa_domain = isl_union_pw_aff_domain(upa); // takes upa
  pa_domains = isl_union_set_get_set_list(upa_domain);
  upa_domain = isl_union_set_free(upa_domain);
  upa = isl_union_pw_aff_empty_ctx(ctx);
  isl_size num_sets = isl_set_list_n_set(pa_domains);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    isl_pw_aff *pa = fn(pa_domains, set_idx, pa_idx, coeff, value);
    upa = isl_union_pw_aff_add_pw_aff(upa, pa);
  }
  pa_domains = isl_set_list_free(pa_domains);
  mupa = isl_multi_union_pw_aff_from_union_pw_aff(upa);
  mupa = isl_multi_union_pw_aff_set_tuple_id(mupa, isl_dim_out, id);
  return isl_schedule_node_band_shift(node, mupa);
}

static __isl_give isl_pw_aff *
__mul_pa_int(__isl_take isl_pw_aff *pa, long coeff) {
  isl_ctx *ctx = isl_pw_aff_get_ctx(pa);
  isl_set *set = isl_pw_aff_domain(isl_pw_aff_copy(pa));
  isl_val *v = isl_val_int_from_si(ctx, coeff);
  return isl_pw_aff_mul(pa, isl_pw_aff_val_on_domain(set, v));
}

static __isl_give isl_pw_aff *
_full_pa_val(__isl_take isl_set_list *sets, isl_size set_loop_idx, int pa_idx,
             long val, long _) {
  isl_set *set = isl_set_list_get_at(sets, set_loop_idx);
  isl_ctx *ctx = isl_set_get_ctx(set);
  return isl_pw_aff_val_on_domain(set, isl_val_int_from_si(ctx, val));
}

static __isl_give isl_pw_aff *
_partial_pa_val(__isl_take isl_set_list *sets, isl_size set_loop_idx,
                int pa_idx, long val, long _) {
  isl_set *set = isl_set_list_get_at(sets, set_loop_idx);
  isl_ctx *ctx = isl_set_get_ctx(set);
  if (set_loop_idx != pa_idx)
    val = 0;
  return isl_pw_aff_val_on_domain(set, isl_val_int_from_si(ctx, val));
}

__isl_give isl_schedule_node *
tadashi_full_shift_val(__isl_take isl_schedule_node *node, long val) {
  isl_multi_union_pw_aff *mupa;
  isl_union_pw_aff *upa;
  isl_union_set *domain;
  isl_id *id;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  id = isl_multi_union_pw_aff_get_tuple_id(mupa, isl_dim_out);
  assert(isl_multi_union_pw_aff_dim(mupa, isl_dim_out) == 1);
  upa = isl_multi_union_pw_aff_get_at(mupa, 0);
  mupa = isl_multi_union_pw_aff_free(mupa);
  domain = isl_union_pw_aff_domain(upa);
  upa = isl_union_pw_aff_val_on_domain(domain, isl_val_int_from_si(ctx, val));
  mupa = isl_multi_union_pw_aff_from_union_pw_aff(upa);
  mupa = isl_multi_union_pw_aff_set_tuple_id(mupa, isl_dim_out, id);
  return isl_schedule_node_band_shift(node, mupa);
}

__isl_give isl_schedule_node *
tadashi_partial_shift_val(__isl_take isl_schedule_node *node, int pa_idx,
                          long val) {
  return _tadashi_shift(node, _partial_pa_val, pa_idx, val, 0);
}

static __isl_give isl_pw_aff *
_full_pa_var(__isl_take isl_set_list *sets, isl_size set_loop_idx, int pa_idx,
             long coeff, long id_idx) {
  isl_set *set = isl_set_list_get_at(sets, set_loop_idx);
  isl_space *space = isl_set_get_space(set);
  isl_local_space *ls = isl_local_space_from_space(space); //
  set = isl_set_free(set);
  isl_pw_aff *pa = isl_pw_aff_var_on_domain(ls, isl_dim_out, id_idx); //
  return __mul_pa_int(pa, coeff);
}

static __isl_give isl_pw_aff *
_partial_pa_var(__isl_take isl_set_list *sets, isl_size set_loop_idx,
                int pa_idx, long coeff, long id_idx) {
  if (set_loop_idx != pa_idx) {
    isl_set *set = isl_set_list_get_at(sets, set_loop_idx);
    isl_val *zero = isl_val_zero(isl_set_get_ctx(set));
    return isl_pw_aff_val_on_domain(set, zero);
  }
  return _full_pa_var(sets, set_loop_idx, pa_idx, coeff, id_idx);
}

__isl_give isl_schedule_node *
tadashi_full_shift_var(__isl_take isl_schedule_node *node, long coeff,
                       long var_idx) {
  return _tadashi_shift(node, _full_pa_var, 0, coeff, var_idx);
}

__isl_give isl_schedule_node *
tadashi_partial_shift_var(__isl_take isl_schedule_node *node, int pa_idx,
                          long coeff, long id_idx) {
  return _tadashi_shift(node, _partial_pa_var, pa_idx, coeff, id_idx);
}

static __isl_give isl_pw_aff *
_full_pa_param(__isl_take isl_set_list *sets, isl_size set_loop_idx, int pa_idx,
               long coeff, long param_idx) {
  isl_set *set = isl_set_list_get_at(sets, set_loop_idx);
  isl_space *space = isl_set_get_space(set);
  isl_id *id = isl_space_get_dim_id(space, isl_dim_param, param_idx);
  space = isl_space_free(space);
  isl_pw_aff *pa = isl_pw_aff_param_on_domain_id(set, id);
  return __mul_pa_int(pa, coeff);
}

static __isl_give isl_pw_aff *
_partial_pa_param(__isl_keep isl_set_list *sets, isl_size set_loop_idx,
                  int pa_idx, long coeff, long param_idx) {
  if (set_loop_idx != pa_idx) {
    isl_set *set = isl_set_list_get_at(sets, set_loop_idx);
    isl_val *zero = isl_val_zero(isl_set_get_ctx(set));
    return isl_pw_aff_val_on_domain(set, zero);
  }
  return _full_pa_param(sets, set_loop_idx, pa_idx, coeff, param_idx);
}

__isl_give isl_schedule_node *
tadashi_full_shift_param(__isl_take isl_schedule_node *node, long coeff,
                         long param_idx) {
  return _tadashi_shift(node, _full_pa_param, 0, coeff, param_idx);
}

__isl_give isl_schedule_node *
tadashi_partial_shift_param(__isl_take isl_schedule_node *node, int pa_idx,
                            long coeff, long param_idx) {
  return _tadashi_shift(node, _partial_pa_param, pa_idx, coeff, param_idx);
}

__isl_give isl_schedule_node *
tadashi_set_parallel(__isl_take isl_schedule_node *node) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  return isl_schedule_node_insert_mark(node,
                                       isl_id_read_from_str(ctx, "parallel"));
}
// sink & order?
