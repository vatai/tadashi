#include <assert.h>
#include <iostream>

#include <isl/flow.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>

#include "ccscop.h"

// === PET RELATED HELPER FUNCTIONS ===================================== //
// ====================================================================== //

;
/* Is "stmt" not a kill statement? */
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
  // isl_union_pw_multi_aff *tagger;

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
  isl_union_map *reads, *may_writes, *kills, *must_writes;
  // *must_source,
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

static __isl_give isl_union_map *
get_dependencies(__isl_keep struct pet_scop *scop) {
  isl_union_map *dep;
  isl_union_flow *flow;
  flow = _get_flow_from_scop(scop);
  dep = isl_union_flow_get_may_dependence(flow);
  isl_union_flow_free(flow);
  return dep;
}

// === METHOD IMPLEMETATIONS ============================================ //
// ====================================================================== //

ccScop::ccScop()
    : schedule(nullptr),     // 1.
      dep_flow(nullptr),     // 2.
      domain(nullptr),       // 3.
      call(nullptr),         // 4.
      may_writes(nullptr),   // 5.
      must_writes(nullptr),  // 6.
      must_kills(nullptr),   // 7.
      may_reads(nullptr),    // 8.
      live_out(nullptr),     // 9.
      current_node(nullptr), // 10.
      tmp_node(nullptr),     // 11.
      current_legal(true),   // 12.
      tmp_legal(true),       // 13.
      modified(0)            // 14.
{
#ifndef NDEBUG
  std::cout << ">>> [c]Default()" << std::endl;
#endif // NDEBUG
}

ccScop::ccScop(pet_scop *ps)
    : schedule(nullptr),     // 1.
      dep_flow(nullptr),     // 2.
      domain(nullptr),       // 3.
      call(nullptr),         // 4.
      may_writes(nullptr),   // 5.
      must_writes(nullptr),  // 6.
      must_kills(nullptr),   // 7.
      may_reads(nullptr),    // 8.
      live_out(nullptr),     // 9.
      current_node(nullptr), // 10.
      tmp_node(nullptr),     // 11.
      current_legal(true),   // 12.
      tmp_legal(true),       // 13.
      modified(0)            // 14.
{
#ifndef NDEBUG
  std::cout << ">>> [c]PetPtr()" << std::endl;
#endif // NDEBUG
  this->schedule = pet_scop_get_schedule(ps);
  this->dep_flow = get_dependencies(ps);
  this->domain = collect_non_kill_domains(ps);
  this->call = collect_call_domains(ps);
  this->may_writes = pet_scop_get_may_writes(ps);
  this->must_writes = pet_scop_get_must_writes(ps);
  this->must_kills = pet_scop_get_must_kills(ps);
  this->may_reads = pet_scop_get_may_reads(ps);
  this->_pet_compute_live_out();
  if (this->domain == nullptr)
    this->domain = isl_schedule_get_domain(this->schedule);
  else
    this->_pet_eliminate_dead_code();
  this->current_node = isl_schedule_get_root(this->schedule);
  if (ps != nullptr)
    pet_scop_free(ps);
}

void
ccScop::_dealloc() {
  // 14-12 need no freeing!
  if (this->tmp_node != nullptr) { // 11.
    isl_schedule_node_free(this->tmp_node);
    this->tmp_node = nullptr;
  }
  if (this->current_node != nullptr) { // 10.
    isl_schedule_node_free(this->current_node);
    this->current_node = nullptr;
  }
  if (this->live_out != nullptr) { // 9.
    isl_union_map_free(this->live_out);
    this->live_out = nullptr;
  }
  if (this->may_reads != nullptr) { // 8.
    isl_union_map_free(this->may_reads);
    this->may_reads = nullptr;
  }
  if (this->must_kills != nullptr) { // 7.
    isl_union_map_free(this->must_kills);
    this->must_kills = nullptr;
  }
  if (this->must_writes != nullptr) { // 6.
    isl_union_map_free(this->must_writes);
    this->must_writes = nullptr;
  }
  if (this->may_writes != nullptr) { // 5.
    isl_union_map_free(this->may_writes);
    this->may_writes = nullptr;
  }
  if (this->call != nullptr) { // 4.
    isl_union_set_free(this->call);
    this->call = nullptr;
  }
  if (this->domain != nullptr) { // 3.
    isl_union_set_free(this->domain);
    this->domain = nullptr;
  }
  if (this->dep_flow != nullptr) { // 2.
    isl_union_map_free(this->dep_flow);
    this->dep_flow = nullptr;
  }
  if (this->schedule != nullptr) { // 1.
    isl_schedule_free(this->schedule);
    this->schedule = nullptr;
  }
}

ccScop::~ccScop() {
#ifndef NDEBUG
  std::cout << "<<< [~]***destructor***()" << std::endl;
#endif // NDEBUG
  this->_dealloc();
}

void
ccScop::_copy(const ccScop &other) {
  this->_dealloc();
  if (other.schedule != nullptr) // 1.
    this->schedule = isl_schedule_copy(other.schedule);
  if (other.dep_flow != nullptr) // 2.
    this->dep_flow = isl_union_map_copy(other.dep_flow);
  if (other.domain != nullptr) // 3.
    this->domain = isl_union_set_copy(other.domain);
  if (other.call != nullptr) // 4.
    this->call = isl_union_set_copy(other.call);
  if (other.may_writes != nullptr) // 5.
    this->may_writes = isl_union_map_copy(other.may_writes);
  if (other.must_writes != nullptr) // 6.
    this->must_writes = isl_union_map_copy(other.must_writes);
  if (other.must_kills != nullptr) // 7.
    this->must_kills = isl_union_map_copy(other.must_kills);
  if (other.may_reads != nullptr) // 8.
    this->may_reads = isl_union_map_copy(other.may_reads);
  if (other.live_out != nullptr) // 9.
    this->live_out = isl_union_map_copy(other.live_out);
  if (other.current_node != nullptr) // 10.
    this->current_node = isl_schedule_node_copy(other.current_node);
  if (other.tmp_node != nullptr) // 11.
    this->tmp_node = isl_schedule_node_copy(other.tmp_node);
  this->current_legal = other.current_legal; // 12.
  this->tmp_legal = other.tmp_legal;         // 13.
  this->modified = other.modified;           // 14.
}

ccScop::ccScop(const ccScop &other)
    : schedule(nullptr),     // 1.
      dep_flow(nullptr),     // 2.
      domain(nullptr),       // 3.
      call(nullptr),         // 4.
      may_writes(nullptr),   // 5.
      must_writes(nullptr),  // 6.
      must_kills(nullptr),   // 7.
      may_reads(nullptr),    // 8.
      live_out(nullptr),     // 9.
      current_node(nullptr), // 10.
      tmp_node(nullptr),     // 11.
      current_legal(true),   // 12.
      tmp_legal(true),       // 13.
      modified(0)            // 14.
{
#ifndef NDEBUG
  std::cout << ">>> [c]Copy()" << std::endl;
#endif // NDEBUG
  this->_copy(other);
}

void
ccScop::_set_nullptr(ccScop *scop) {
  scop->schedule = nullptr;     // 1.
  scop->dep_flow = nullptr;     // 2.
  scop->domain = nullptr;       // 3.
  scop->call = nullptr;         // 4.
  scop->may_writes = nullptr;   // 5.
  scop->must_writes = nullptr;  // 6.
  scop->must_kills = nullptr;   // 7.
  scop->may_reads = nullptr;    // 8.
  scop->live_out = nullptr;     // 9.
  scop->current_node = nullptr; // 10.
  scop->tmp_node = nullptr;     // 11.
  scop->current_legal = true;   // 12.
  scop->tmp_legal = true;       // 13.
  scop->modified = 0;           // 14.
}

ccScop::ccScop(ccScop &&other) noexcept
    : schedule(other.schedule),           // 1.
      dep_flow(other.dep_flow),           // 2.
      domain(other.domain),               // 3.
      call(other.call),                   // 4.
      may_writes(other.may_writes),       // 5.
      must_writes(other.must_writes),     // 6.
      must_kills(other.must_kills),       // 7.
      may_reads(other.may_reads),         // 8.
      live_out(other.live_out),           // 9.
      current_node(other.current_node),   // 10.
      tmp_node(other.tmp_node),           // 11.
      current_legal(other.current_legal), // 12.
      tmp_legal(other.tmp_legal),         // 13.
      modified(other.modified)            // 14.
{
#ifndef NDEBUG
  std::cout << ">>> [c]Move()" << std::endl;
#endif // NDEBUG
  _set_nullptr(&other);
}

ccScop &
ccScop::operator=(const ccScop &other) {
#ifndef NDEBUG
  std::cout << ">>> [op=]Copy()" << std::endl;
#endif // NDEBUG
  if (this == &other)
    return *this;
  this->_copy(other);
  return *this;
}

ccScop &
ccScop::operator=(ccScop &&other) noexcept {
#ifndef NDEBUG
  std::cout << ">>> [op=]Move()" << std::endl;
#endif // NDEBUG
  if (this == &other)
    return *this;
  this->_dealloc();
  this->schedule = other.schedule;           // 1.
  this->dep_flow = other.dep_flow;           // 2.
  this->domain = other.domain;               // 3.
  this->call = other.call;                   // 4.
  this->may_writes = other.may_writes;       // 5.
  this->must_writes = other.must_writes;     // 6.
  this->must_kills = other.must_kills;       // 7.
  this->may_reads = other.may_reads;         // 8.
  this->live_out = other.live_out;           // 9.
  this->current_node = other.current_node;   // 10.
  this->tmp_node = other.tmp_node;           // 11.
  this->current_legal = other.current_legal; // 12.
  this->tmp_legal = other.tmp_legal;         // 13.
  this->modified = other.modified;           // 14.
  //
  _set_nullptr(&other);
  return *this;
}

void
ccScop::rollback() {
  if (!this->modified)
    return;
  std::swap(this->current_legal, this->tmp_legal);
  std::swap(this->current_node, this->tmp_node);
}

void
ccScop::reset() {
  if (!this->modified)
    return;
  this->current_node = isl_schedule_node_free(this->current_node);
  this->current_node = isl_schedule_get_root(this->schedule);
  this->current_legal = true;
  this->tmp_node = isl_schedule_node_free(this->tmp_node);
  this->tmp_node = nullptr;
  this->tmp_legal = false;
  this->modified = false;
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

bool
ccScop::check_legality() {
  isl_union_map *dep = isl_union_map_copy(this->dep_flow);
  isl_schedule *schedule = isl_schedule_node_get_schedule(this->current_node);
  isl_union_map *map = isl_schedule_get_map(schedule);
  isl_schedule_free(schedule);
  return _check_legality(map, dep);
}

bool
tadashi_check_legality_parallel(__isl_keep isl_schedule_node *node,
                                __isl_take isl_union_map *dep) {
  isl_union_map *map;
  bool retval;
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
