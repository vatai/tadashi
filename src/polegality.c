#include <assert.h>
#include <isl/ast.h>
#include <isl/schedule_node.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/arg.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/id.h>
#include <isl/map.h>
#include <isl/options.h>
#include <isl/point.h>
#include <isl/schedule.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/space_type.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include <pet.h>

struct options {
  struct isl_options *isl;
  struct pet_options *pet;
  char *schedule;
  char *source_file;
  unsigned tree;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, source_file, "source file", 0)
ISL_ARG_STR(struct options, schedule, 's', "schedule", "schedule", 0,
            "Yaml file describing the schedule")
ISL_ARGS_END

ISL_ARG_DEF(options, struct options, options_args)

__isl_give isl_union_flow *get_flow_from_scop(__isl_keep pet_scop *scop) {
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

__isl_give isl_union_set *
get_zeros_on_union_set(__isl_take isl_union_set *delta_uset) {
  isl_set *delta_set;
  isl_multi_aff *ma;

  delta_set = isl_set_from_union_set(delta_uset);
  ma = isl_multi_aff_zero(isl_set_get_space(delta_set));
  isl_set_free(delta_set);
  return isl_union_set_from_set(isl_set_from_multi_aff(ma));
}

__isl_give isl_union_map *get_dependencies(pet_scop *scop) {
  isl_union_map *dep;
  isl_union_flow *flow;
  flow = get_flow_from_scop(scop);
  dep = isl_union_flow_get_may_dependence(flow);
  isl_union_flow_free(flow);
  return dep;
}

isl_bool check_legality(isl_ctx *ctx, char *schedule_str,
                        __isl_take isl_union_map *dep) {
  isl_union_map *domain, *schedule_map, *le;
  isl_union_set *delta, *zeros;

  schedule_map = isl_union_map_read_from_str(ctx, schedule_str);

  domain = isl_union_map_apply_domain(dep, isl_union_map_copy(schedule_map));
  domain = isl_union_map_apply_range(domain, schedule_map);
  delta = isl_union_map_deltas(domain);

  zeros = get_zeros_on_union_set(isl_union_set_copy(delta));

  le = isl_union_set_lex_le_union_set(delta, zeros);
  isl_bool retval = isl_union_map_is_empty(le);
  isl_union_map_free(le);
  return retval;
}

void print_legality(char *schedule_str, isl_bool legal) {
  printf("The schedule %s is %scorrect!\n", schedule_str,
         (legal ? "" : "not "));
}

void codegen(isl_ctx *ctx, char *schedule_str) {
  isl_ast_build *build;
  isl_ast_node *ast;
  isl_schedule *schedule = isl_schedule_read_from_str(ctx, schedule_str);
  // build = isl_ast_build_alloc(ctx);
  // assert(build != NULL);
  // ast = isl_ast_build_node_from_schedule(build, isl_schedule_copy(schedule));
  // printf("code:\n%s\n", isl_ast_node_to_C_str(ast));
  // isl_ast_node_free(ast);
  // isl_ast_build_free(build);
  isl_schedule_free(schedule);
}

int main(int argc, char *argv[]) {
  struct options *options = options_new_with_defaults();
  options_parse(options, argc, argv, ISL_ARG_ALL);
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);

  pet_scop *scop = pet_scop_extract_from_C_source(ctx, options->source_file, 0);
  if (!scop) {
    printf("No scop found!\n");
    isl_ctx_free(ctx);
    return -1;
  }

  if (options->schedule) {
    isl_union_map *dependencies = get_dependencies(scop);
    isl_bool legal = check_legality(ctx, options->schedule, dependencies);
    print_legality(options->schedule, legal);
    codegen(ctx, options->schedule);
    isl_union_map_free(dependencies);
  } else {
    isl_schedule *schedule = pet_scop_get_schedule(scop);
    isl_schedule_node *root = isl_schedule_get_root(schedule);
    printf("%s\n", isl_schedule_node_to_str(root));
    isl_schedule_node_free(root);
    isl_schedule_free(schedule);
  }

  pet_scop_free(scop);
  isl_ctx_free(ctx);
  return 0;
}
