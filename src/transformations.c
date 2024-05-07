
#include <assert.h>
#include <isl/aff_type.h>
#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/space.h>
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

isl_schedule_node *tadashi_fuse(isl_schedule_node *node) { return node; }

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
tadashi_partial_shift_id(__isl_take isl_schedule_node *node, int pa_idx,
                         long id_idx) {
  return _shift_partial(node, _pa_id, pa_idx, id_idx);
}

__isl_give isl_schedule_node *
tadashi_partial_shift_val(__isl_take isl_schedule_node *node, int pa_idx,
                          long id_idx) {
  return _shift_partial(node, _pa_val, pa_idx, id_idx);
}

// sink & order?
