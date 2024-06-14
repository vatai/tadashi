#include <assert.h>
#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/space.h>
#include <isl/space_type.h>
#include <isl/union_set.h>

#include <isl/val.h>
#include <isl/val_type.h>
#include <pet.h>

#include "transformations.h"

isl_schedule_node *tadashi_tile(isl_schedule_node *node, int tile_size) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  return isl_schedule_node_band_tile(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, tile_size))));
}

isl_schedule_node *tadashi_interchange(isl_schedule_node *node) {
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
tadashi_complete_fuse(__isl_take isl_schedule_node *node) {
  // To merge all band node children of a sequence,
  //
  // take their partial schedules,
  //
  // intersect them with the corresponding filters and
  //
  // take the union.

  // Introduce a new band node on top of the sequence
  // using

  // If you want, you can then also delete the original band nodes,
  // but this is not strictly required since they will mostly be
  // ignored during AST generation.
  printf("%s\n", isl_schedule_node_to_str(node));
  isl_size num_children = isl_schedule_node_n_children(node);
  node = isl_schedule_node_first_child(node);
  isl_multi_union_pw_aff *mupa = NULL;
  for (isl_size i = 0; i < num_children; i++) {
    isl_union_set *filter;
    isl_multi_union_pw_aff *tmp;
    assert(isl_schedule_node_get_type(node) == isl_schedule_node_filter);
    filter = isl_schedule_node_filter_get_filter(node);
    node = isl_schedule_node_first_child(node);
    printf("f: %s\n", isl_union_set_to_str(filter));
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
  /* isl_schedule *sched; */
  /* sched = isl_schedule_node_get_schedule(node); */
  /* sched = isl_schedule_insert_partial_schedule(sched, mupa); */
  /* node = isl_schedule_get_root(sched); */
  node = isl_schedule_node_insert_partial_schedule(node, mupa);
  printf("%s\n", isl_schedule_node_to_str(node));
  return node;
}

__isl_give isl_schedule_node *tadashi_fuse(__isl_take isl_schedule_node *node,
                                           int idx1, int idx2) {
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
  node = _fuse_insert_outer_shorter_sequence(node, idx1, idx2);
  printf("BEFORE: %s\n", isl_schedule_node_to_str(node));
  /* node = isl_schedule_node_parent(node); */
  /* node = isl_schedule_node_parent(node); */
  /* return node; */
  //  go to original, inner, longer sequence
  // node = isl_schedule_node_child(node, idx1);
  // node = isl_schedule_node_first_child(node);
  // filters = isl_union_set_list_alloc(ctx, 2);
  // node = _fuse_get_filter_and_mupa(node, idx1, &result[0], &filters);
  // node = _fuse_get_filter_and_mupa(node, idx2, &result[1], &filters);
  // mupa = isl_multi_union_pw_aff_union_add(result[0].mupa, result[1].mupa);
  // node = isl_schedule_node_insert_sequence(node, filters);
  // node = isl_schedule_node_insert_partial_schedule(node, mupa);
  // node = isl_schedule_node_parent(node);
  // node = isl_schedule_node_parent(node);
  return node;
}

isl_schedule_node *tadashi_scale(isl_schedule_node *node, long scale) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  node = isl_schedule_node_band_scale(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, scale))));
  return node;
}

__isl_give isl_pw_aff *_pa_val(__isl_take isl_set *set, long val) {
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_val *v = isl_val_int_from_si(ctx, val);
  return isl_pw_aff_val_on_domain(set, v);
}

__isl_give isl_pw_aff *_pa_id(__isl_take isl_set *set, long id_idx) {
  isl_space *space = isl_set_get_space(set);
  set = isl_set_free(set);
  isl_size ndims = isl_space_dim(space, isl_dim_out);
  space = isl_space_add_dims(space, isl_dim_in, ndims);
  for (int i = 0; i < ndims; ++i) {
    isl_id *id = isl_space_get_dim_id(space, isl_dim_out, i);
    space = isl_space_set_dim_id(space, isl_dim_in, i, id);
  }
  const char *name = isl_space_get_tuple_name(space, isl_dim_out);
  space = isl_space_set_tuple_name(space, isl_dim_in, name);
  isl_multi_aff *ma = isl_multi_aff_identity(space);
  isl_aff *aff = isl_multi_aff_get_at(ma, id_idx);
  ma = isl_multi_aff_free(ma);
  return isl_pw_aff_from_aff(aff);
}

__isl_give isl_schedule_node *_shift_partial(
    __isl_take isl_schedule_node *node,
    __isl_give isl_pw_aff *(*fn)(__isl_take isl_set *set, long const_val),
    int idx, long const_val) {
  isl_multi_union_pw_aff *mupa;
  isl_union_pw_aff *upa;
  isl_union_set *upa_domain;
  isl_set_list *pa_domains;
  isl_id *id;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  id = isl_multi_union_pw_aff_get_tuple_id(mupa, isl_dim_out);
  isl_size mupa_dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_out);
  assert(mupa_dim == 1);
  upa = isl_multi_union_pw_aff_get_at(mupa, 0);
  mupa = isl_multi_union_pw_aff_free(mupa);
  upa_domain = isl_union_pw_aff_domain(upa); // takes upa
  pa_domains = isl_union_set_get_set_list(upa_domain);
  upa_domain = isl_union_set_free(upa_domain);
  upa = isl_union_pw_aff_empty_ctx(ctx);
  isl_size num_sets = isl_set_list_n_set(pa_domains);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    isl_set *set = isl_set_list_get_at(pa_domains, set_idx);
    isl_pw_aff *pa = ((idx == set_idx) ? fn(set, const_val) : _pa_val(set, 0));
    upa = isl_union_pw_aff_add_pw_aff(upa, pa);
  }
  pa_domains = isl_set_list_free(pa_domains);
  mupa = isl_multi_union_pw_aff_from_union_pw_aff(upa);
  mupa = isl_multi_union_pw_aff_set_tuple_id(mupa, isl_dim_out, id);
  return isl_schedule_node_band_shift(node, mupa);
}

__isl_give isl_schedule_node *
tadashi_partial_shift_var(__isl_take isl_schedule_node *node, int pa_idx,
                          long id_idx) {
  return _shift_partial(node, _pa_id, pa_idx, id_idx);
}

__isl_give isl_schedule_node *
tadashi_partial_shift_val(__isl_take isl_schedule_node *node, int pa_idx,
                          long id_idx) {
  return _shift_partial(node, _pa_val, pa_idx, id_idx);
}

__isl_give isl_schedule_node *
tadashi_full_shift_var(__isl_take isl_schedule_node *node, int pa_idx,
                       long id_idx) {
  return _shift_partial(node, _pa_id, pa_idx, id_idx);
}

__isl_give isl_schedule_node *
tadashi_full_shift_val(__isl_take isl_schedule_node *node, int pa_idx,
                       long id_idx) {
  return _shift_partial(node, _pa_val, pa_idx, id_idx);
}

// sink & order?
