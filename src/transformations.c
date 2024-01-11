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

isl_bool chk_single_tile() { return isl_bool_true; }

isl_schedule_node *single_tile(isl_ctx *ctx, isl_schedule_node *node, int si) {
  isl_space *space = isl_schedule_node_band_get_space(node);
  isl_val_list *val_list = isl_val_list_from_val(isl_val_int_from_si(ctx, si));
  isl_multi_val *mv = isl_multi_val_from_val_list(space, val_list);
  return isl_schedule_node_band_tile(node, mv);
}

isl_bool foreach_node(isl_schedule_node *node, void *user) {
  struct user_t *u = user;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  printf("Node:%lu\n", u->node_counter);
  if (u->node_counter == 2) {
    if (isl_schedule_node_get_type(node) == isl_schedule_node_band) {
      node = single_tile(ctx, node, 4);
    }
    // TODO Figure out what to do with tile which changes the tree.
    return isl_bool_false;
  }
  u->node_counter++;
  return isl_bool_true;
};

__isl_give isl_schedule *interactive_transform(isl_ctx *ctx,
                                               __isl_keep struct pet_scop *scop,
                                               struct user_t *user) {

  isl_schedule *schedule = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(schedule);
  user->node_counter = 0;
  // isl_schedule_node_dump(node);
  isl_schedule_node_foreach_descendant_top_down(node, foreach_node, user);

  // isl_schedule_node_dump(node);
  isl_schedule_node_free(node);
  return schedule;
}
