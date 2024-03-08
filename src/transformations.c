#include "transformations.h"

#include <isl/aff_type.h>
#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/union_set.h>

#include <isl/val.h>
#include <isl/val_type.h>
#include <pet.h>
#include <string.h>

isl_schedule_node *tadashi_tile_1d(isl_schedule_node *node, int si) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  isl_space *space = isl_schedule_node_band_get_space(node);
  isl_val_list *val_list = isl_val_list_from_val(isl_val_int_from_si(ctx, si));
  isl_multi_val *mv = isl_multi_val_from_val_list(space, val_list);
  return isl_schedule_node_band_tile(node, mv);
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

isl_schedule_node *tadashi_scale(isl_schedule_node *node) { return node; }

isl_schedule_node *tadashi_shift(isl_schedule_node *node) { return node; }

// sink & order?
