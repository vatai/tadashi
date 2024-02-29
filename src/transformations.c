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

isl_bool tadashi_tile_1d_check() { return isl_bool_true; }

isl_schedule_node *tadashi_tile_1d(isl_schedule_node *node, int si) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  isl_space *space = isl_schedule_node_band_get_space(node);
  isl_val_list *val_list = isl_val_list_from_val(isl_val_int_from_si(ctx, si));
  isl_multi_val *mv = isl_multi_val_from_val_list(space, val_list);
  return isl_schedule_node_band_tile(node, mv);
}

isl_bool tadashi_fuse_chk() { return isl_bool_true; }
isl_schedule_node *tadashi_fuse(isl_schedule_node *node, int si) {
  return node;
}

// interchange

// scale

// shift

// sink & order?
