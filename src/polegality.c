#include <isl/union_map.h>
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

  polegality(&args, scop);

  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("DONE!\n");
  printf("Hello, world!\n");
  return 0;
}
