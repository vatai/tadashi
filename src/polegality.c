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

isl_stat fn(__isl_take isl_map *map, void *user) {
  isl_space *space = isl_map_get_space(map);
  isl_multi_val *mv = isl_multi_val_zero(isl_space_copy(space));
  isl_multi_aff_multi_val_on_domain_space(isl_space_copy(space),
                                          isl_multi_val_copy(mv));
  printf("!mv: %s\n", isl_multi_val_to_str(mv));
  printf("!map: %s\n", isl_map_to_str(map));
  isl_multi_val_free(mv);
  isl_space_free(space);
  isl_map_free(map);
  return isl_stat_ok;
};

void compute_dependencies(isl_ctx *ctx, pet_scop *scop) {
  isl_union_map *dep, *domain, *schedule_map, *le, *delta_map;
  isl_union_set *delta, *zeros, *range;
  isl_schedule *schedule;
  isl_union_flow *flow;
  isl_space *space;
  int correct;

  flow = get_flow_from_scop(scop);
  schedule = pet_scop_get_schedule(scop);

  dep = isl_union_flow_get_may_dependence(flow);

  /* schedule_map = isl_schedule_get_map(schedule); */
  /* isl_union_map_foreach_map(schedule_map, fn, 0); */
  /* isl_union_map_free(schedule_map); */

  schedule_map =
      isl_union_map_read_from_str(ctx, "[N] -> { S_0[i, j] -> [j, i] }");
  zeros = isl_union_set_read_from_str(ctx, "[N] -> { [0, 0] }");
  printf("sch: %s\n", isl_union_map_to_str(schedule_map));
  printf("dep: %s\n", isl_union_map_to_str(dep));

  domain = isl_union_map_apply_domain(isl_union_map_copy(dep),
                                      isl_union_map_copy(schedule_map));
  domain = isl_union_map_apply_range(domain, isl_union_map_copy(schedule_map));
  delta = isl_union_map_deltas(isl_union_map_copy(domain));
  delta_map = isl_union_map_deltas_map(isl_union_map_copy(domain));
  isl_union_map_foreach_map(delta_map, fn, 0);
  printf("domain: %s\n", isl_union_map_to_str(domain));
  printf("delta: %s\n", isl_union_set_to_str(delta));
  le = isl_union_set_lex_le_union_set(isl_union_set_copy(delta),
                                      isl_union_set_copy(zeros));
  printf("The schedule is %scorrect!\n",
         (isl_union_map_is_empty(le) ? "" : "not "));

  isl_union_map_free(delta_map);
  isl_union_map_free(le);
  isl_union_set_free(delta);
  isl_union_set_free(zeros);
  isl_union_map_free(domain);
  isl_union_map_free(dep);
  isl_union_map_free(schedule_map);
  isl_schedule_free(schedule);
  isl_union_flow_free(flow);
}

void polegality(struct Args *args, pet_scop *scop) {
  isl_union_map *schedule_map = isl_schedule_get_map(scop->schedule);
  printf("original schedule: %s\n", isl_union_map_to_str(schedule_map));

  isl_union_map *may_reads = pet_scop_get_may_reads(scop);
  printf("may reads: %s\n", isl_union_map_to_str(may_reads));

  isl_union_map *may_writes = pet_scop_get_may_writes(scop);
  printf("may writes: %s\n", isl_union_map_to_str(may_writes));

  isl_union_map *must_writes = pet_scop_get_must_writes(scop);
  printf("must writes: %s\n", isl_union_map_to_str(must_writes));

  isl_union_map *result = isl_union_map_apply_range(
      isl_union_map_copy(may_reads),
      isl_union_map_reverse(isl_union_map_copy(may_writes)));
  printf("result: %s\n", isl_union_map_to_str(result));
  result = isl_union_map_apply_range(result, isl_union_map_copy(schedule_map));
  printf("result: %s\n", isl_union_map_to_str(result));

  isl_union_map_free(result);
  isl_union_map_free(must_writes);
  isl_union_map_free(may_writes);
  isl_union_map_free(may_reads);
  isl_union_map_free(schedule_map);
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

  // polegality(&args, scop);
  compute_dependencies(ctx, scop);

  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("DONE!\n");
  printf("Hello, world!\n");
  return 0;
}
