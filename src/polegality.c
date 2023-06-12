#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/id.h>
#include <isl/map.h>
#include <isl/point.h>
#include <isl/schedule.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/space_type.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>
#include <stdio.h>

#include <isl/options.h>
#include <pet.h>

char FILENAME[] = "../examples/depnodep.cc";
char SCHEDULE[] = "NONE";

struct options {
  struct isl_options *isl;
  struct pet_options *pet;
  char *schedule;
  char *code;
  unsigned tree;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, schedule, "schedule", NULL)
ISL_ARG_ARG(struct options, code, "code", NULL)
ISL_ARG_BOOL(struct options, tree, 0, "tree", 0,
             "input schedule is specified as schedule tree")
ISL_ARGS_END

ISL_ARG_DEF(options, struct options, options_args)

struct Args {
  char *filename;
  char *schedule;
};

struct Args get_args(int argc, char *argv[]) {
  struct Args args;
  if (argc == 1) {
    args.filename = FILENAME;
    args.schedule = SCHEDULE;
    return args;
  }

  if (argc < 3) {
    printf("Usage: %s <C/C++ source file> <schedule>\n", argv[0]);
    exit(-1);
  }
  args.filename = argv[1];
  args.schedule = argv[2];
  return args;
}

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

isl_bool compute_dependencies(char *schedule_str, isl_ctx *ctx,
                              pet_scop *scop) {
  isl_union_map *dep, *domain, *schedule_map, *le;
  isl_union_set *delta, *zeros, *range;
  isl_schedule *schedule;
  isl_union_flow *flow;
  isl_space *space;
  int correct;

  flow = get_flow_from_scop(scop);
  schedule = pet_scop_get_schedule(scop);

  dep = isl_union_flow_get_may_dependence(flow);
  printf("dep: %s\n", isl_union_map_to_str(dep));

  schedule_map = isl_union_map_read_from_str(ctx, schedule_str);
  printf("sch: %s\n", isl_union_map_to_str(schedule_map));

  domain = isl_union_map_apply_domain(isl_union_map_copy(dep),
                                      isl_union_map_copy(schedule_map));
  domain = isl_union_map_apply_range(domain, isl_union_map_copy(schedule_map));
  printf("domain: %s\n", isl_union_map_to_str(domain));

  delta = isl_union_map_deltas(isl_union_map_copy(domain));
  printf("delta: %s\n", isl_union_set_to_str(delta));

  isl_set *dset = isl_set_from_union_set(isl_union_set_copy(delta));
  printf("dset: %s\n", isl_set_to_str(dset));
  space = isl_set_get_space(dset);
  isl_set_free(dset);
  printf("space: %s\n", isl_space_to_str(space));
  isl_multi_aff *ma = isl_multi_aff_zero(space);
  printf("ma: %s\n", isl_multi_aff_to_str(ma));
  isl_set *zset = isl_set_from_multi_aff(ma);
  printf("zset: %s\n", isl_set_to_str(zset));
  zeros = isl_union_set_from_set(zset);

  le = isl_union_set_lex_le_union_set(isl_union_set_copy(delta),
                                      isl_union_set_copy(zeros));
  isl_bool retval = isl_union_map_is_empty(le);

  isl_union_map_free(le);
  isl_union_set_free(delta);
  isl_union_set_free(zeros);
  isl_union_map_free(domain);
  isl_union_map_free(dep);
  isl_union_map_free(schedule_map);
  isl_schedule_free(schedule);
  isl_union_flow_free(flow);
  return retval;
}

void check_schedule(char *schedule_str, isl_ctx *ctx, pet_scop *scop) {
  isl_bool legal = compute_dependencies(schedule_str, ctx, scop);
  printf("The schedule %s is %scorrect!\n", schedule_str,
         (legal ? "" : "not "));
}

int main(int argc, char *argv[]) {
  struct Args args = get_args(argc, argv);
  printf("Input file: %s\n", args.filename);
  printf("Input schedule %s\n", args.schedule);
  struct options *options = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);
  pet_scop *scop = pet_scop_extract_from_C_source(ctx, args.filename, 0);
  if (!scop) {
    printf("No scop found!\n");
    isl_ctx_free(ctx);
    return -1;
  }
  check_schedule("[N] -> { S_0[i, j] -> [j, i] }", ctx, scop);
  check_schedule("[N] -> { S_0[i, j] -> [j, -i] }", ctx, scop);

  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("DONE!\n");
  printf("Hello, world!\n");
  return 0;
}
