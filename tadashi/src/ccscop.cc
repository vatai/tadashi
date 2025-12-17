#include <assert.h>
#include <iostream>

#include <isl/flow.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>

#include "ccscop.h"

// ====================================================================== //
// === PET RELATED HELPER FUNCTIONS ===================================== //
// ====================================================================== //

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
  int *has_call = (int *)user;

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
  int *has_call = (int *)user;

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
void
ccScop::_pet_compute_live_out() {
  isl_schedule *schedule;
  isl_union_map *kills;
  isl_union_map *exposed;
  isl_union_map *covering;
  isl_union_access_info *access;
  isl_union_flow *flow;

  schedule = isl_schedule_copy(this->schedule);
  kills = isl_union_map_union(isl_union_map_copy(this->must_writes),
                              isl_union_map_copy(this->must_kills));
  access = isl_union_access_info_from_sink(kills);
  access = isl_union_access_info_set_may_source(
      access, isl_union_map_copy(this->may_writes));
  access = isl_union_access_info_set_schedule(access, schedule);
  flow = isl_union_access_info_compute_flow(access);
  covering = isl_union_flow_get_full_may_dependence(flow);
  isl_union_flow_free(flow);

  covering = isl_union_map_range_factor_range(covering);
  exposed = isl_union_map_copy(this->may_writes);
  exposed = isl_union_map_subtract(exposed, covering);
  this->live_out = exposed;
}

static __isl_give isl_union_set *
shared_constraints(__isl_take isl_union_set *old,
                   __isl_take isl_union_set *extended) {
  isl_union_set *hull, *gist;

  hull = isl_union_set_plain_unshifted_simple_hull(old);
  gist = isl_union_set_copy(hull);
  gist = isl_union_set_gist(gist, extended);
  return isl_union_set_gist(hull, gist);
}

void
ccScop::_pet_eliminate_dead_code() {
  isl_union_set *live;
  isl_union_map *dep;
  isl_union_pw_multi_aff *tagger;

  live = isl_union_map_domain(isl_union_map_copy(this->live_out));
  if (!isl_union_set_is_empty(this->call)) {
    live = isl_union_set_union(live, isl_union_set_copy(this->call));
    live = isl_union_set_coalesce(live);
  }

  dep = isl_union_map_copy(this->dep_flow);
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
    live = isl_union_set_intersect(live, isl_union_set_copy(this->domain));
    live = isl_union_set_union(live, other_space);
  }

  isl_union_map_free(dep);

  /* report_dead_code(ps, live); */

  this->domain =
      isl_union_set_intersect(this->domain, isl_union_set_copy(live));
  this->schedule =
      isl_schedule_intersect_domain(this->schedule, isl_union_set_copy(live));
  this->dep_flow = isl_union_map_intersect_range(this->dep_flow, live);
  /* tagger = isl_union_pw_multi_aff_copy(ps->tagger); */
  /* live = isl_union_set_preimage_union_pw_multi_aff(live, tagger); */
  /* ps->tagged_dep_flow = isl_union_map_intersect_range(ps->tagged_dep_flow, */
  /* 					live); */
}

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

// ====================================================================== //
// === METHOD IMPLEMETATIONS ============================================ //
// ====================================================================== //

ccScop::~ccScop() {
#ifndef NDEBUG
  std::cout << "<<< [d]Default()";
  dealloc();
  std::cout << std::endl;
#endif // NDEBUG
}

ccScop::ccScop()
    : current_node(nullptr), tmp_node(nullptr), current_legal(true),
      tmp_legal(true), modified(0), domain(nullptr), call(nullptr),
      may_writes(nullptr), must_writes(nullptr), must_kills(nullptr),
      may_reads(nullptr), live_out(nullptr), schedule(nullptr),
      _pet_scop(nullptr) {
#ifndef NDEBUG
  std::cout << ">>> [c]Default()" << std::endl;
#endif // NDEBUG
}

ccScop::ccScop(pet_scop *ps)
    : current_node(nullptr), tmp_node(nullptr), current_legal(true),
      tmp_legal(true), modified(0), domain(nullptr), call(nullptr),
      may_writes(nullptr), must_writes(nullptr), must_kills(nullptr),
      may_reads(nullptr), live_out(nullptr), schedule(nullptr),
      _pet_scop(nullptr) {
#ifndef NDEBUG
  std::cout << ">>> [c]PetPtr()" << std::endl;
#endif // NDEBUG
  isl_schedule *sched = pet_scop_get_schedule(ps);
  this->current_node = isl_schedule_get_root(sched);
  isl_schedule_free(sched);
  this->domain = collect_non_kill_domains(ps);
  this->call = collect_call_domains(ps);
  this->may_writes = pet_scop_get_may_writes(ps);
  this->must_writes = pet_scop_get_must_writes(ps);
  this->must_kills = pet_scop_get_must_kills(ps);
  this->may_reads = pet_scop_get_may_reads(ps);
  this->schedule = schedule;
  this->_pet_compute_live_out();
  this->dep_flow = get_dependencies(ps);
  if (this->domain == nullptr)
    this->domain = isl_schedule_get_domain(this->schedule);
  else
    this->_pet_eliminate_dead_code();
  this->_pet_scop = ps;
}

void
ccScop::dealloc() {
  if (this->current_node != nullptr)
    this->current_node = isl_schedule_node_free(this->current_node);
  if (this->tmp_node != nullptr)
    this->tmp_node = isl_schedule_node_free(this->tmp_node);
  this->domain = isl_union_set_free(this->domain);
  if (this->call != nullptr)
    this->call = isl_union_set_free(this->call);
  if (this->may_writes != nullptr)
    this->may_writes = isl_union_map_free(this->may_writes);
  if (this->must_writes != nullptr)
    this->must_writes = isl_union_map_free(this->must_writes);
  if (this->must_kills != nullptr)
    this->must_kills = isl_union_map_free(this->must_kills);
  if (this->may_reads != nullptr)
    this->may_reads = isl_union_map_free(this->may_reads);
  this->schedule = isl_schedule_free(this->schedule);
  if (this->dep_flow != nullptr)
    this->dep_flow = isl_union_map_free(this->dep_flow);
  if (this->live_out != nullptr)
    this->live_out = isl_union_map_free(this->live_out);
  if (this->_pet_scop != nullptr)
    this->_pet_scop = pet_scop_free(this->_pet_scop);
}
