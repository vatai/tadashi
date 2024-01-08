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

void dim_names(isl_schedule_node *node) {
  const char *name;
  isl_multi_union_pw_aff *mupa;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  name = isl_multi_union_pw_aff_get_tuple_name(mupa, isl_dim_out);
  // TODO save name
  isl_union_set *domain = isl_multi_union_pw_aff_domain(mupa);
  isl_size num_sets = isl_union_set_n_set(domain);
  isl_set_list *slist = isl_union_set_get_set_list(domain);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    isl_set *set = isl_set_list_get_at(slist, set_idx);
    isl_size num_dims = isl_set_dim(set, isl_dim_set);
    for (isl_size di = 0; di < num_dims; di++) {
      name = isl_set_get_dim_name(set, isl_dim_set, di);
      size_t len = strlen(name);
      // TODO save name
    }
    isl_set_free(set);
  }
  isl_set_list_free(slist);
  isl_union_set_free(domain);
}

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
