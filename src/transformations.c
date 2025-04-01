/** @file */
#include <assert.h>
#include <isl/aff_type.h>
#include <limits.h>

#include <isl/aff.h>
#include <isl/constraint.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/ilp.h>
#include <isl/local_space.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include <pet.h>

#include "transformations.h"

/**
 * Insert a context node with param_idx to be less than
 * limit.
 *
 * @param node Node of the schedule tree
 * @param param_idx Parameter index
 * @param limit Upper limit for parameter specified by param_idx
 * @returns Node pointing to the node below the context
 */
isl_schedule_node *
limit_param_with_context(isl_schedule_node *node, int param_idx, int limit) {
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

/**
 * 1D loop tiling.
 *
 * @param node The band node which represents the loop which will be tiled
 * @param tile_size Size of (number of iterations in) one tile
 * @returns Transformed schedule tree node
 */
isl_schedule_node *
tadashi_tile(isl_schedule_node *node, int tile_size) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  return isl_schedule_node_band_tile(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, tile_size))));
}

__isl_give isl_schedule_node *
tadashi_unroll(__isl_take isl_schedule_node *node, int factor) {
  node = tadashi_tile(node, factor);
  node = isl_schedule_node_parent(node);

  // =====
  // begin
  // =====

  isl_multi_union_pw_aff *mupa;
  isl_space *space;
  isl_union_set *domain, *restriction;
  isl_union_map *map;

  mupa = isl_schedule_node_band_get_partial_schedule(node);
  map =
      isl_union_map_from_multi_union_pw_aff(isl_multi_union_pw_aff_copy(mupa));
  domain = isl_union_map_domain(isl_union_map_copy(map));

  isl_schedule *schedule = isl_schedule_node_get_schedule(node);
  domain = isl_union_set_intersect(domain, isl_schedule_get_domain(schedule));
  domain = isl_union_set_apply(domain, isl_union_map_copy(map));
  // the good stuff

  printf("domain: %s\n", isl_union_set_to_str(domain));
  printf("range: %s\n", isl_union_set_to_str(isl_union_map_range(map)));

  // get boundaries

  /* printf("set?!: %s\n", isl_set_to_str(isl_set_from_union_set(domain))); */
  domain = isl_union_set_project_out(domain, isl_dim_param, 1, 1);
  printf("domain again: %s\n", isl_union_set_to_str(domain));
  /* printf("space:%s\n", isl_space_to_str(isl_union_set_get_space(domain))); */
  /* isl_union_pw_multi_aff *upma = isl_union_pw_multi_aff_from_domain(domain);
   */
  /* printf("upma: %s\n", isl_union_pw_multi_aff_to_str(upma)); */

  /* isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, 0); */
  /* isl_val *v = isl_union_pw_aff_max_val(upa); */
  /* printf("val: %s\n", isl_val_to_str(v)); */

  /* printf("upa: %s\n", isl_union_pw_aff_to_str(upa)); */
  /* isl_pw_aff_list *pal = isl_union_pw_aff_get_pw_aff_list(upa); */
  /* isl_pw_aff *pa = isl_pw_aff_list_get_at(pal, 0); */
  /* printf("pa: %s\n", isl_pw_aff_to_str(pa)); */
  /* isl_set *set = isl_set_from_pw_aff(pa); */
  /* printf("set: %s\n", isl_set_to_str(set)); */
  /* isl_aff *aff = isl_pw_aff_as_aff(pa); */
  /* printf("aff: %s\n", isl_aff_to_str(aff)); */

  /* isl_constraint *cst = isl_inequality_from_aff(aff); */
  /* isl_constraint_dump(cst); */

  // isl_constraint_get_coefficient_val()

  // ===
  // end
  // ===

  /* node = isl_schedule_node_band_member_set_ast_loop_type(node, 0, */
  /*                                                        isl_ast_loop_separate);
   */
  node = isl_schedule_node_first_child(node);
  /* node = isl_schedule_node_band_member_set_ast_loop_type(node, 0, */
  /*                                                        isl_ast_loop_separate);
   */
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_band_member_set_ast_loop_type(node, 0,
                                                         isl_ast_loop_unroll);
  return node;
}

__isl_give isl_schedule_node *
tadashi_full_unroll(__isl_take isl_schedule_node *node) {
  return node;
}

/**
 * Loop interchange.
 *
 * @param node The band node which will be swapped with it's only child
 * @returns Transformed schedule tree node
 */
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

static __isl_give isl_schedule_node *
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

__isl_give isl_schedule_node *
tadashi_full_fuse(__isl_take isl_schedule_node *node) {
  // To merge all band node children of a sequence, take their partial
  // schedules, intersect them with the corresponding filters and take
  // the union.

  // Introduce a new band node on top of the sequence using If you
  // want, you can then also delete the original band nodes, but this
  // is not strictly required since they will mostly be ignored during
  // AST generation.
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

static __isl_give isl_union_set_list *
alloc_half_list(isl_schedule_node **node, int begin, int end) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(*node);
  isl_union_set_list *list = isl_union_set_list_alloc(ctx, end - begin);
  for (int pos = begin; pos < end; pos++) {
    *node = isl_schedule_node_child(*node, pos);
    isl_union_set *domain = isl_schedule_node_filter_get_filter(*node);
    list = isl_union_set_list_add(list, domain);
    *node = isl_schedule_node_parent(*node);
  }
  return list;
  // return isl_union_set_list_union(list);
}

static __isl_give isl_schedule_node *
make_subsequence(__isl_take isl_schedule_node *node,
                 __isl_take isl_union_set *set,
                 __isl_take isl_union_set_list *list) {
  isl_union_map *map;
  isl_multi_union_pw_aff *mupa;
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  map = isl_schedule_node_get_subtree_schedule_union_map(node);
  map = isl_union_map_intersect_domain(map, set);
  node = isl_schedule_node_cut(node);
  mupa = isl_multi_union_pw_aff_from_union_map(map);
  node = isl_schedule_node_insert_partial_schedule(node, mupa);
  node = isl_schedule_node_insert_sequence(node, list);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);
  return node;
}

int
tadashi_valid_split(__isl_keep isl_schedule_node *node, int split) {
  enum isl_schedule_node_type type;
  type = isl_schedule_node_get_type(node);
  // The node is a sequence or set node
  if (type != isl_schedule_node_sequence && type != isl_schedule_node_set)
    return 0;
  // 1 <= split <= n-1
  size_t num_children = isl_schedule_node_n_children(node);
  if (!(0 < split && split < num_children))
    return 0;
  // Parent is a band node.
  type = isl_schedule_node_get_parent_type(node);
  if (type != isl_schedule_node_band)
    return 0;
  return 1;
}

__isl_give isl_schedule_node *
tadashi_split(__isl_take isl_schedule_node *node, int split) {
  isl_union_set_list *filters, *left, *right;
  isl_union_set *lefts, *rights;
  assert(tadashi_valid_split(node, split));
  isl_size num_children = isl_schedule_node_n_children(node);
  left = alloc_half_list(&node, 0, split);
  right = alloc_half_list(&node, split, num_children);
  lefts = isl_union_set_list_union(isl_union_set_list_copy(left));
  rights = isl_union_set_list_union(isl_union_set_list_copy(right));
  filters = isl_union_set_list_from_union_set(isl_union_set_copy(lefts));
  filters = isl_union_set_list_add(filters, isl_union_set_copy(rights));
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_insert_sequence(node, filters);
  node = isl_schedule_node_first_child(node);
  node = make_subsequence(node, lefts, left);
  node = isl_schedule_node_next_sibling(node);
  node = make_subsequence(node, rights, right);
  node = isl_schedule_node_parent(node);
  return node;
}

int
tadashi_valid_full_split(__isl_keep isl_schedule_node *node) {
  enum isl_schedule_node_type node_type;
  node_type = isl_schedule_node_get_parent_type(node);
  // Parent is a band node.
  if (isl_schedule_node_band != node_type)
    return 0;
  // This is a sequence or set node.
  node_type = isl_schedule_node_get_type(node);
  if (node_type != isl_schedule_node_sequence &&
      node_type != isl_schedule_node_set)
    return 0;
  return 1;
}

__isl_give isl_schedule_node *
tadashi_full_split(__isl_take isl_schedule_node *node) {
  assert(tadashi_valid_full_split(node));
  isl_multi_union_pw_aff *mupa;
  node = isl_schedule_node_parent(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  node = isl_schedule_node_delete(node);
  isl_size num_children = isl_schedule_node_n_children(node);
  for (int pos = 0; pos < num_children; pos++) {
    isl_multi_union_pw_aff *tmp;
    node = isl_schedule_node_child(node, pos);
    isl_union_set *domain = isl_schedule_node_filter_get_filter(node);
    tmp = isl_multi_union_pw_aff_intersect_domain(
        isl_multi_union_pw_aff_copy(mupa), domain);
    node = isl_schedule_node_first_child(node);
    node = isl_schedule_node_insert_partial_schedule(node, tmp);
    node = isl_schedule_node_parent(node);
    node = isl_schedule_node_parent(node);
  }
  isl_multi_union_pw_aff_free(mupa);
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
tadashi_set_parallel(__isl_take isl_schedule_node *node, int num_threads) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  char pragma[LINE_MAX];
  sprintf(pragma, "pragma_parallel_%d", num_threads);
  return isl_schedule_node_insert_mark(node, isl_id_read_from_str(ctx, pragma));
}
// sink & order?
