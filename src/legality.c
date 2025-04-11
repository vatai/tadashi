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

/* Is "stmt" not a kill statement?
 */
static int
is_not_kill(struct pet_stmt *stmt) {
  return !pet_stmt_is_kill(stmt);
}

/* Collect the iteration domains of the statements in "scop" that
 * satisfy "pred".
 */
static __isl_give isl_union_set *
collect_domains(struct pet_scop *scop, int (*pred)(struct pet_stmt *stmt)) {
  int i;
  isl_set *domain_i;
  isl_union_set *domain;

  if (!scop)
    return NULL;

  domain = isl_union_set_empty(isl_set_get_space(scop->context));

  for (i = 0; i < scop->n_stmt; ++i) {
    struct pet_stmt *stmt = scop->stmts[i];

    if (!pred(stmt))
      continue;

    if (stmt->n_arg > 0) {
      printf("loc: %d\n", pet_loc_get_line(scop->loc));
      isl_die(isl_union_set_get_ctx(domain), isl_error_unsupported,
              "data dependent conditions not supported",
              return isl_union_set_free(domain));
    }

    domain_i = isl_set_copy(scop->stmts[i]->domain);
    domain = isl_union_set_add_set(domain, domain_i);
  }

  return domain;
}

/* Collect the iteration domains of the statements in "scop",
 * skipping kill statements.
 */
static __isl_give isl_union_set *
collect_non_kill_domains(struct pet_scop *scop) {
  return collect_domains(scop, &is_not_kill);
}

/* This function is used as a callback to pet_expr_foreach_call_expr
 * to detect if there is any call expression in the input expression.
 * Assign the value 1 to the integer that "user" points to and
 * abort the search since we have found what we were looking for.
 */
static int
set_has_call(__isl_keep pet_expr *expr, void *user) {
  int *has_call = user;

  *has_call = 1;

  return -1;
}

/* Does "expr" contain any call expressions?
 */
static int
expr_has_call(__isl_keep pet_expr *expr) {
  int has_call = 0;

  if (pet_expr_foreach_call_expr(expr, &set_has_call, &has_call) < 0 &&
      !has_call)
    return -1;

  return has_call;
}

/* This function is a callback for pet_tree_foreach_expr.
 * If "expr" contains any call (sub)expressions, then set *has_call
 * and abort the search.
 */
static int
check_call(__isl_keep pet_expr *expr, void *user) {
  int *has_call = user;

  if (expr_has_call(expr))
    *has_call = 1;

  return *has_call ? -1 : 0;
}

/* Does "stmt" contain any call expressions?
 */
static int
has_call(struct pet_stmt *stmt) {
  int has_call = 0;

  if (pet_tree_foreach_expr(stmt->body, &check_call, &has_call) < 0 &&
      !has_call)
    return -1;

  return has_call;
}

/* Collect the iteration domains of the statements in "scop"
 * that contain a call expression.
 */
static __isl_give isl_union_set *
collect_call_domains(struct pet_scop *scop) {
  return collect_domains(scop, &has_call);
}

/* Compute the live out accesses, i.e., the writes that are
 * potentially not killed by any kills or any other writes, and
 * store them in ps->live_out.
 *
 * We compute the "dependence" of any "kill" (an explicit kill
 * or a must write) on any may write.
 * The elements accessed by the may writes with a "depending" kill
 * also accessing the element are definitely killed.
 * The remaining may writes can potentially be live out.
 *
 * The result of the dependence analysis is
 *
 *	{ IW -> [IK -> A] }
 *
 * with IW the instance of the write statement, IK the instance of kill
 * statement and A the element that was killed.
 * The range factor range is
 *
 *	{ IW -> A }
 *
 * containing all such pairs for which there is a kill statement instance,
 * i.e., all pairs that have been killed.
 */
static void
compute_live_out(struct tadashi_scop *ts) {
  isl_schedule *schedule;
  isl_union_map *kills;
  isl_union_map *exposed;
  isl_union_map *covering;
  isl_union_access_info *access;
  isl_union_flow *flow;

  schedule = isl_schedule_copy(ts->schedule);
  kills = isl_union_map_union(isl_union_map_copy(ts->must_writes),
                              isl_union_map_copy(ts->must_kills));
  access = isl_union_access_info_from_sink(kills);
  access = isl_union_access_info_set_may_source(
      access, isl_union_map_copy(ts->may_writes));
  access = isl_union_access_info_set_schedule(access, schedule);
  flow = isl_union_access_info_compute_flow(access);
  covering = isl_union_flow_get_full_may_dependence(flow);
  isl_union_flow_free(flow);

  covering = isl_union_map_range_factor_range(covering);
  exposed = isl_union_map_copy(ts->may_writes);
  exposed = isl_union_map_subtract(exposed, covering);
  ts->live_out = exposed;
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

struct tadashi_scop *
allocate_tadashi_scop(struct pet_scop *ps) {
  struct tadashi_scop *ts = malloc(sizeof(struct tadashi_scop));
  ts->domain = collect_non_kill_domains(ps);
  ts->call = collect_call_domains(ps);
  ts->may_writes = pet_scop_get_may_writes(ps);
  ts->must_writes = pet_scop_get_must_writes(ps);
  ts->must_kills = pet_scop_get_must_kills(ps);
  ts->schedule = isl_schedule_copy(ps->schedule);
  compute_live_out(ts);
  ts->dep_flow = get_dependencies(ps);
  if (ts->domain == NULL)
    ts->domain = isl_schedule_get_domain(ts->schedule);
  else
    eliminate_dead_code(ts);
  ts->pet_scop = ps;
  return ts;
}

void
free_tadashi_scop(struct tadashi_scop *ts) {
  ts->domain = isl_union_set_free(ts->domain);
  ts->call = isl_union_set_free(ts->call);
  ts->may_writes = isl_union_map_free(ts->may_writes);
  ts->must_writes = isl_union_map_free(ts->must_writes);
  ts->must_kills = isl_union_map_free(ts->must_kills);
  ts->schedule = isl_schedule_free(ts->schedule);
  ts->dep_flow = isl_union_map_free(ts->dep_flow);
  ts->live_out = isl_union_map_free(ts->live_out);
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
