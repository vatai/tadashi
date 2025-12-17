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

#include <pet.h>

#include "legality.h"

static __isl_give isl_union_flow *
_get_flow_from_scop(__isl_keep pet_scop *scop) {
  isl_union_map *reads, *may_writes, *must_source, *kills, *must_writes;
  isl_union_access_info *access;
  isl_schedule *schedule;
  isl_union_flow *flow;
  reads = pet_scop_get_may_reads(scop);
  access = isl_union_access_info_from_sink(reads);

  kills = pet_scop_get_must_kills(scop);
  must_writes = pet_scop_get_tagged_must_writes(scop);
  kills = isl_union_map_union(kills, must_writes);
  access = isl_union_access_info_set_kill(access, kills);

  may_writes = pet_scop_get_may_writes(scop);
  access = isl_union_access_info_set_may_source(access, may_writes);

  /* must_source = pet_scop_get_must_writes(scop); */
  /* access = isl_union_access_info_set_must_source(access, must_source); */

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
shared_constraints(__isl_take isl_union_set *old,
                   __isl_take isl_union_set *extended) {
  isl_union_set *hull, *gist, *valid;

  hull = isl_union_set_plain_unshifted_simple_hull(old);
  gist = isl_union_set_copy(hull);
  gist = isl_union_set_gist(gist, extended);
  return isl_union_set_gist(hull, gist);
}

static void
eliminate_dead_code(struct tadashi_scop *ts) {
  isl_union_set *live;
  isl_union_map *dep;
  isl_union_pw_multi_aff *tagger;

  live = isl_union_map_domain(isl_union_map_copy(ts->live_out));
  if (!isl_union_set_is_empty(ts->call)) {
    live = isl_union_set_union(live, isl_union_set_copy(ts->call));
    live = isl_union_set_coalesce(live);
  }

  dep = isl_union_map_copy(ts->dep_flow);
  dep = isl_union_map_reverse(dep);

  for (;;) {
    isl_union_set *extra, *universe, *same_space, *other_space;
    isl_union_set *prev, *valid;

    extra =
        isl_union_set_apply(isl_union_set_copy(live), isl_union_map_copy(dep));
    if (isl_union_set_is_subset(extra, live)) {
      isl_union_set_free(extra);
      break;
    }

    universe = isl_union_set_universe(isl_union_set_copy(live));
    same_space = isl_union_set_intersect(isl_union_set_copy(extra),
                                         isl_union_set_copy(universe));
    other_space = isl_union_set_subtract(extra, universe);

    prev = isl_union_set_copy(live);
    live = isl_union_set_union(live, same_space);
    valid = shared_constraints(prev, isl_union_set_copy(live));

    live = isl_union_set_affine_hull(live);
    live = isl_union_set_intersect(live, valid);
    live = isl_union_set_intersect(live, isl_union_set_copy(ts->domain));
    live = isl_union_set_union(live, other_space);
  }

  isl_union_map_free(dep);

  /* report_dead_code(ps, live); */

  ts->domain = isl_union_set_intersect(ts->domain, isl_union_set_copy(live));
  ts->schedule =
      isl_schedule_intersect_domain(ts->schedule, isl_union_set_copy(live));
  ts->dep_flow = isl_union_map_intersect_range(ts->dep_flow, live);
  /* tagger = isl_union_pw_multi_aff_copy(ps->tagger); */
  /* live = isl_union_set_preimage_union_pw_multi_aff(live, tagger); */
  /* ps->tagged_dep_flow = isl_union_map_intersect_range(ps->tagged_dep_flow, */
  /* 					live); */
}

isl_bool
pw_aff_is_cst(__isl_keep isl_pw_aff *pa, void *_) {
  return isl_pw_aff_is_cst(pa);
}

isl_union_set *
idx_to_domain(isl_union_set *set, void *user) {
  isl_union_map *map = (isl_union_map *)user;
  return isl_union_set_apply(set, isl_union_map_copy(map));
}

isl_stat
add_singleton_to_list(__isl_take isl_point *pnt, void *user) {
  isl_union_set_list **filters = (isl_union_set_list **)user;
  isl_union_set *singleton = isl_union_set_from_point(pnt);
  *filters = isl_union_set_list_add(*filters, singleton);
  return isl_stat_ok;
}

int
filter_cmp(struct isl_union_set *set1, struct isl_union_set *set2, void *_) {
  isl_point *p1 = isl_union_set_sample_point(isl_union_set_copy(set1));
  isl_val *v1 = isl_point_get_coordinate_val(p1, isl_dim_all, 0);
  isl_point *p2 = isl_union_set_sample_point(isl_union_set_copy(set2));
  isl_val *v2 = isl_point_get_coordinate_val(p2, isl_dim_all, 0);
  int result = isl_val_get_num_si(v1) - isl_val_get_num_si(v2);
  isl_point_free(p1);
  isl_point_free(p2);
  isl_val_free(v1);
  isl_val_free(v2);
  return result;
}

__isl_give isl_schedule *
_umap_to_schedule_tree(__isl_take isl_union_set *domain,
                       __isl_take isl_union_map *umap) {
  isl_multi_union_pw_aff *mupa;
  isl_schedule *schedule;
  isl_schedule_node *root;
  isl_union_map *map;
  isl_ctx *ctx = isl_union_set_get_ctx(domain);
  schedule = isl_schedule_from_domain(domain);
  mupa = isl_multi_union_pw_aff_from_union_map(umap);
  root = isl_schedule_get_root(schedule);
  schedule = isl_schedule_free(schedule);
  root = isl_schedule_node_first_child(root);
  isl_size dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_out);
  for (int pos = dim - 1; pos >= 0; pos--) {
    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, pos);
    if (isl_union_pw_aff_every_pw_aff(upa, pw_aff_is_cst, NULL)) {
      map = isl_union_map_from_union_pw_aff(upa);
      map = isl_union_map_reverse(map);
      isl_union_set *steps = isl_union_map_domain(isl_union_map_copy(map));
      isl_union_set_list *filters = isl_union_set_list_alloc(ctx, 1);
      isl_union_set_foreach_point(steps, add_singleton_to_list, &filters);
      filters = isl_union_set_list_sort(filters, filter_cmp, map);
      isl_union_set_list_map(filters, idx_to_domain, map);
      root = isl_schedule_node_insert_sequence(root, filters);
      isl_union_set_free(steps);
      isl_union_map_free(map);
    } else {
      isl_multi_union_pw_aff *tmp =
          isl_multi_union_pw_aff_from_union_pw_aff(upa);
      root = isl_schedule_node_insert_partial_schedule(root, tmp);
    }
  }

  isl_multi_union_pw_aff_free(mupa);
  schedule = isl_schedule_node_get_schedule(root);
  isl_schedule_node_free(root);
  return schedule;
}

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

void
free_tadashi_scop(struct tadashi_scop *ts) {
  ts->domain = isl_union_set_free(ts->domain);
  if (ts->call != NULL)
    ts->call = isl_union_set_free(ts->call);
  if (ts->may_writes != NULL)
    ts->may_writes = isl_union_map_free(ts->may_writes);
  if (ts->must_writes != NULL)
    ts->must_writes = isl_union_map_free(ts->must_writes);
  if (ts->must_kills != NULL)
    ts->must_kills = isl_union_map_free(ts->must_kills);
  if (ts->may_reads != NULL)
    ts->may_reads = isl_union_map_free(ts->may_reads);
  ts->schedule = isl_schedule_free(ts->schedule);
  if (ts->dep_flow != NULL)
    ts->dep_flow = isl_union_map_free(ts->dep_flow);
  if (ts->live_out != NULL)
    ts->live_out = isl_union_map_free(ts->live_out);
  if (ts->pet_scop != NULL)
    ts->pet_scop = pet_scop_free(ts->pet_scop);
  free(ts);
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
tadashi_check_legality(__isl_keep isl_schedule_node *node,
                       __isl_take isl_union_map *dep) {
  isl_bool legal;
  isl_union_pw_multi_aff *dep_upma;
  isl_schedule *schedule = isl_schedule_node_get_schedule(node);
  isl_union_map *map = isl_schedule_get_map(schedule);
  isl_schedule_free(schedule);
  return _check_legality(map, dep);
}

isl_bool
tadashi_check_legality_parallel(__isl_keep isl_schedule_node *node,
                                __isl_take isl_union_map *dep) {
  isl_union_map *map;
  isl_bool retval;
  isl_union_map *domain, *cmp;
  isl_union_set *delta, *zeros;
  node = isl_schedule_node_first_child(node);
  map = isl_schedule_node_band_get_partial_schedule_union_map(node);
  node = isl_schedule_node_parent(node);

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
  retval = isl_union_map_is_empty(cmp);
  cmp = isl_union_map_free(cmp);
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
