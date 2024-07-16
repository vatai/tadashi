#include <assert.h>
#include <isl/space_type.h>
#include <isl/union_map_type.h>
#include <isl/val_type.h>
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

static __isl_give isl_union_flow *
get_flow_from_scop(__isl_keep pet_scop *scop) {
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
  flow = get_flow_from_scop(scop);
  dep = isl_union_flow_get_may_dependence(flow);
  isl_union_flow_free(flow);
  return dep;
}

static __isl_give isl_union_set *
get_zeros_on_union_set(__isl_take isl_union_set *delta_uset) {
  isl_set *delta_set;
  isl_multi_aff *ma;

  delta_set = isl_set_from_union_set(delta_uset);
  ma = isl_multi_aff_zero(isl_set_get_space(delta_set));
  isl_set_free(delta_set);
  return isl_union_set_from_set(isl_set_from_multi_aff(ma));
}

isl_bool
check_legality(isl_ctx *ctx, __isl_take isl_union_map *schedule_map,
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
  zeros = get_zeros_on_union_set(isl_union_set_copy(delta));
  le = isl_union_set_lex_le_union_set(delta, zeros);
  isl_bool retval = isl_union_map_is_empty(le);
  isl_union_map_free(le);
  return retval;
}

isl_stat
delta_set_lexpos(__isl_take isl_set *set, void *user) {
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
calculate_delta(__isl_keep isl_schedule_node *node,
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

isl_bool
legality_test(__isl_keep isl_schedule_node *node, void *user) {
  enum isl_schedule_node_type type;
  isl_union_map *le;
  isl_union_set *delta;
  isl_union_map *dep = user;
  type = isl_schedule_node_get_type(node);
  switch (type) {
  case isl_schedule_node_band:
    delta = calculate_delta(node, dep);
    isl_union_set_foreach_set(delta, delta_set_lexpos, NULL);
    isl_union_set_free(delta);
    break;
  }

  return isl_bool_true;
}

isl_bool
check_schedule_legality(isl_ctx *ctx, __isl_keep isl_schedule *schedule,
                        __isl_take isl_union_map *dep) {
  isl_bool legal;
  isl_schedule_node *root;
  isl_union_pw_multi_aff *dep_upma;
  root = isl_schedule_get_root(schedule);
  // dep_upma = isl_union_pw_multi_aff_from_union_map(isl_union_map_copy(dep));
  // legal = isl_schedule_node_every_descendant(root, legality_test, dep);
  // isl_union_pw_multi_aff_free(dep_upma);
  isl_schedule_node_free(root);
  isl_union_map *map = isl_schedule_get_map(schedule);
  // printf("schedule as union map:\n%s\n", isl_union_map_to_str(map));
  return check_legality(ctx, map, dep);
}
