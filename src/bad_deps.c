#include <assert.h>
#include <isl/ast.h>
#include <isl/schedule_type.h>
#include <isl/union_map.h>
#include <stdio.h>

#include <isl/ast_build.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/union_set.h>
#include <pet.h>

/* get dependencies (for legality check) */

static __isl_give isl_union_flow *
_get_raw_flow(__isl_keep pet_scop *scop) {
  isl_union_map *reads, *may_writes, *must_source, *kills, *must_writes;
  isl_union_access_info *access;
  isl_schedule *schedule;
  isl_union_flow *flow;
  reads = pet_scop_get_may_reads(scop);
  access = isl_union_access_info_from_sink(reads);

  kills = pet_scop_get_must_kills(scop);
  must_writes = pet_scop_get_must_writes(scop);
  kills = isl_union_map_union(kills, must_writes);
  access = isl_union_access_info_set_kill(access, kills);

  may_writes = pet_scop_get_may_writes(scop);
  access = isl_union_access_info_set_may_source(access, may_writes);

  must_source = pet_scop_get_must_writes(scop);
  access = isl_union_access_info_set_must_source(access, must_source);

  schedule = pet_scop_get_schedule(scop);
  access = isl_union_access_info_set_schedule(access, schedule);

  flow = isl_union_access_info_compute_flow(access);
  return flow;
}

__isl_give isl_union_map *
get_dependencies(__isl_keep struct pet_scop *scop,
                 __isl_give isl_union_flow *(*fn)(__isl_keep pet_scop *scop)) {
  isl_union_map *dep;
  isl_union_flow *flow;
  flow = fn(scop);
  dep = isl_union_flow_get_may_dependence(flow);
  isl_union_flow_free(flow);
  return dep;
}

/* transformation (split) */

static __isl_give isl_union_set_list *
alloc_half_list(isl_schedule_node **node, int begin, int end) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(*node);
  isl_union_set_list *list = isl_union_set_list_alloc(ctx, end - begin);
  for (int pos = begin; pos < end; pos++) {
    *node = isl_schedule_node_child(*node, pos);
    isl_union_set *domain = isl_schedule_node_filter_get_filter(*node);
    list = isl_union_set_list_add(list, domain);
    *node = isl_schedule_node_parent(*node);
  }
  return list;
}

__isl_give isl_schedule_node *
tadashi_split(__isl_take isl_schedule_node *node, int split) {
  isl_union_set_list *filters, *left, *right;
  isl_union_set *lefts, *rights;
  isl_size num_children = isl_schedule_node_n_children(node);

  left = alloc_half_list(&node, 0, split);
  lefts = isl_union_set_list_union(left);
  filters = isl_union_set_list_from_union_set(lefts);

  right = alloc_half_list(&node, split, num_children);
  rights = isl_union_set_list_union(right);
  filters = isl_union_set_list_add(filters, rights);

  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_insert_sequence(node, filters);

  return node;
}

/* legality check */

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
  isl_schedule *schedule = isl_schedule_node_get_schedule(node);
  isl_union_map *map = isl_schedule_get_map(schedule);
  isl_schedule_free(schedule);
  return _check_legality(map, dep);
}

/* main */

int
main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  pet_scop *scop = pet_scop_extract_from_C_source(ctx, "bdi.c", NULL);

  /* get deps */
  isl_union_map *deps = get_dependencies(scop, _get_raw_flow);

  isl_schedule *schedule = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(schedule);
  isl_schedule_free(schedule);

  /* transform schedule tree */
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  node = tadashi_split(node, 1);

  /* check legality */

  assert(tadashi_check_legality(node, deps));

  schedule = isl_schedule_node_get_schedule(node);
  isl_ast_build *build = isl_ast_build_alloc(ctx);
  isl_ast_node *ast = isl_ast_build_node_from_schedule(build, schedule);

  printf("code: %s\n", isl_ast_node_to_C_str(ast));
  return 0;
}
