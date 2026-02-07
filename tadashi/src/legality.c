#include <assert.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include "legality.h"
#include <pet.h>

struct tadashi_scop *
allocate_tadashi_scop_from_json(isl_union_set *domain,
                                isl_union_map *schedule) {
  struct tadashi_scop *ts = malloc(sizeof(struct tadashi_scop));
  ts->domain = isl_union_set_copy(domain);
  ts->call = NULL;
  ts->may_writes = NULL;
  ts->must_writes = NULL;
  ts->must_kills = NULL;
  ts->may_reads = NULL;
  ts->schedule = _umap_to_schedule_tree(domain, schedule);
  ts->dep_flow = NULL;
  ts->live_out = NULL;
  ts->pet_scop = NULL;
  return ts;
}

/* Efficient legality check below */

isl_stat
__delta_set_lexpos(__isl_take isl_set *set, void *user) {
  isl_val *val;
  set = isl_set_lexmin(set);
  isl_size dim = isl_set_dim(set, isl_dim_set);
  unsigned pos = 0;
  val = isl_set_plain_get_val_if_fixed(set, isl_dim_set, pos);
  pos++;
  while (isl_val_is_zero(val) && pos < dim) {
    isl_val_free(val);
    val = isl_set_plain_get_val_if_fixed(set, isl_dim_set, pos);
    pos++;
  }
  isl_bool is_pos = isl_val_is_pos(val);
  isl_set_free(set);
  isl_val_free(val);
  return is_pos ? isl_stat_ok : isl_stat_error;
}

__isl_give isl_union_set *
__calculate_delta(__isl_keep isl_schedule_node *node,
                  __isl_keep isl_union_map *dep) {
  isl_multi_union_pw_aff *mupa;
  isl_union_map *domain, *range;
  isl_union_set *delta;
  isl_union_map *partial;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  partial = isl_union_map_from_multi_union_pw_aff(mupa);
  domain = isl_union_map_apply_domain(isl_union_map_copy(dep),
                                      isl_union_map_copy(partial));
  domain = isl_union_map_apply_range(domain, partial);
  delta = isl_union_map_deltas(domain);
  return delta;
}

static isl_bool
__legality_test(__isl_keep isl_schedule_node *node, void *user) {
  enum isl_schedule_node_type type;
  isl_union_map *le;
  isl_union_set *delta;
  isl_union_map *dep = user;
  type = isl_schedule_node_get_type(node);
  switch (type) {
  case isl_schedule_node_band:
    delta = __calculate_delta(node, dep);
    isl_union_set_foreach_set(delta, __delta_set_lexpos, NULL);
    isl_union_set_free(delta);
    break;
  }

  return isl_bool_true;
}
