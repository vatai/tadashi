#include <assert.h>
#include <isl/union_map.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include <pet.h>

#include "legality.h"

static __isl_give isl_union_flow *
_get_flow_from_scop(__isl_keep pet_scop *scop) {
  isl_union_map *sink, *may_source, *must_source;
  isl_union_access_info *access;
  isl_schedule *schedule;
  isl_union_flow *flow;
  sink = pet_scop_get_may_reads(scop);
  access = isl_union_access_info_from_sink(sink);

  may_source = pet_scop_get_may_writes(scop);
  access = isl_union_access_info_set_may_source(access, may_source);

  must_source = pet_scop_get_must_writes(scop);
  access = isl_union_access_info_set_must_source(access, must_source);

  schedule = pet_scop_get_schedule(scop);
  access = isl_union_access_info_set_schedule(access, schedule);

  flow = isl_union_access_info_compute_flow(access);
  return flow;
}

__isl_give isl_union_map *
get_dependencies(__isl_keep struct pet_scop *scop) {
  isl_union_map *dep;
  isl_union_flow *flow;
  flow = _get_flow_from_scop(scop);
  dep = isl_union_flow_get_may_dependence(flow);
  isl_union_flow_free(flow);
  return dep;
}

static __isl_give isl_union_set *
_get_zeros_on_union_set(__isl_take isl_union_set *delta_uset) {
  isl_set *delta_set;
  isl_multi_aff *ma;

  delta_set = isl_set_from_union_set(delta_uset);
  ma = isl_multi_aff_zero(isl_set_get_space(delta_set));
  isl_set_free(delta_set);
  return isl_union_set_from_set(isl_set_from_multi_aff(ma));
}

static __isl_give isl_bool
_check_legality(__isl_take isl_union_map *schedule_map,
                __isl_take isl_union_map *dep) {
  isl_union_map *domain, *le;
  isl_union_set *delta, *zeros;

  if (isl_union_map_is_empty(dep)) {
    isl_union_map_free(dep);
    isl_union_map_free(schedule_map);
    return isl_bool_true;
  }
  domain = isl_union_map_apply_domain(dep, isl_union_map_copy(schedule_map));
  domain = isl_union_map_apply_range(domain, schedule_map);
  delta = isl_union_map_deltas(domain);
  zeros = _get_zeros_on_union_set(isl_union_set_copy(delta));
  le = isl_union_set_lex_le_union_set(delta, zeros);
  isl_bool retval = isl_union_map_is_empty(le);
  isl_union_map_free(le);
  return retval;
}

isl_bool
tadashi_check_legality(isl_ctx *ctx, __isl_keep isl_schedule *schedule,
                       __isl_take isl_union_map *dep) {
  isl_bool legal;
  isl_union_pw_multi_aff *dep_upma;
  isl_union_map *map = isl_schedule_get_map(schedule);
  return _check_legality(map, dep);
}

isl_bool
tadashi_check_legality_parallel(isl_ctx *ctx,
                                __isl_keep isl_schedule_node *node,
                                __isl_take isl_union_map *dep) {
  isl_union_map *map;
  isl_bool retval;
  map = isl_schedule_node_band_get_partial_schedule_union_map(node);
  isl_union_map *domain, *cmp;
  isl_union_set *delta, *zeros;

  if (isl_union_map_is_empty(dep)) {
    dep = isl_union_map_free(dep);
    map = isl_union_map_free(map);
    return isl_bool_true;
  }
  domain = isl_union_map_apply_domain(dep, isl_union_map_copy(map));
  domain = isl_union_map_apply_range(domain, map);
  delta = isl_union_map_deltas(domain);
  if (isl_union_set_is_empty(delta)) {
    delta = isl_union_set_free(delta);
    return isl_bool_true;
  }
  zeros = _get_zeros_on_union_set(isl_union_set_copy(delta));
  cmp = isl_union_set_lex_lt_union_set(isl_union_set_copy(delta),
                                       isl_union_set_copy(zeros));
  isl_union_map_free(cmp);
  retval = isl_union_map_is_empty(cmp);
  cmp = isl_union_set_lex_gt_union_set(delta, zeros);
  retval = retval && isl_union_map_is_empty(cmp);
  isl_union_map_free(cmp);
  return retval;
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
