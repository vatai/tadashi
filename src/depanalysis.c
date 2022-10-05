#include <stdio.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/map.h>
#include <isl/options.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>

#include <pet.h>

const char filename[] = "../src/hello.c";

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

void depanalysis(pet_scop *scop) {
  printf("--- depanalysis() ---\n");
  isl_set *set = pet_scop_get_context(scop);
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_space *space = isl_space_unit(ctx);
  space = isl_space_add_dims(space, isl_dim_in, 1);
  space = isl_space_add_dims(space, isl_dim_out, 1);

  isl_union_map *sch_map = isl_schedule_get_map(scop->schedule);

  isl_map *identity = isl_map_identity(isl_space_copy(space));
  isl_map *one = isl_map_universe(isl_space_copy(space));
  one = isl_map_fix_si(one, isl_dim_out, 0, -1);
  isl_map *im1 = isl_map_sum(isl_map_copy(identity), isl_map_copy(one));
  printf("\n");
  printf("im1: %s\n", isl_map_to_str(im1));
  printf("sch map: %s\n", isl_union_map_to_str(sch_map));

  isl_union_map *sink = isl_union_map_from_map(isl_map_copy(identity));
  isl_union_access_info *access = isl_union_access_info_from_sink(
      isl_union_map_from_map(isl_map_copy(im1)));
  access = isl_union_access_info_set_schedule(
      access, isl_schedule_copy(scop->schedule));
  isl_union_flow *flow =
      isl_union_access_info_compute_flow(isl_union_access_info_copy(access));

  printf("\n");
  printf("access: %s\n", isl_union_access_info_to_str(access));
  printf("\n");
  printf("flow: %s\n", isl_union_flow_to_str(flow));

  isl_map_free(im1);
  isl_union_map_free(sch_map);
  isl_map_free(identity);
  isl_map_free(one);
  isl_union_flow_free(flow);
  isl_union_access_info_free(access);
  isl_union_map_free(sink);
  isl_space_free(space);
  isl_set_free(set);
  return;
}

int main(int argc, char *argv[]) {
  struct options *options = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);
  pet_scop *scop = pet_scop_extract_from_C_source(ctx, filename, "g");

  depanalysis(scop);

  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("DONE!\n");
}
