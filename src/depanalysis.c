#include <stdio.h>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/id.h>
#include <isl/map.h>
#include <isl/mat.h>
#include <isl/options.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include <pet.h>

const char filename[] = "../examples/hello.c";

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
  printf("\n");
  isl_ctx *ctx;
  isl_id *id;
  isl_map *reads, *writes, *one;
  isl_set *set;
  isl_space *space;
  isl_union_access_info *access;
  isl_union_flow *flow;
  isl_union_map *schedule_map, *may_dep;
  isl_union_set *domain;
  isl_map *map;
  isl_basic_map_list *bml;
  isl_mat *mat;

  set = pet_scop_get_context(scop);
  ctx = isl_set_get_ctx(set);
  printf("set: %s\n", isl_set_to_str(set));

  schedule_map = isl_schedule_get_map(scop->schedule);
  printf("schedule_map: %s\n", isl_union_map_to_str(schedule_map));

  domain = isl_union_map_domain(isl_union_map_copy(schedule_map));
  printf("domain: %s\n", isl_union_set_to_str(domain));

  space = isl_union_set_get_space(domain);
  id = isl_id_alloc(ctx, "S_0", NULL);
  space = isl_space_add_named_tuple_id_ui(space, id, 1);
  id = isl_id_alloc(ctx, "A", NULL);
  space = isl_space_add_named_tuple_id_ui(space, id, 1);
  printf("space: %s\n", isl_space_to_str(space));

  reads = isl_map_identity(isl_space_copy(space));
  printf("reads: %s\n", isl_map_to_str(reads));

  writes = isl_map_identity(isl_space_copy(space));
  one = isl_map_universe(isl_space_copy(space));
  one = isl_map_fix_si(one, isl_dim_out, 0, 1);
  writes = isl_map_sum(writes, isl_map_copy(one));
  printf("writes: %s\n", isl_map_to_str(writes));

  access = isl_union_access_info_from_sink(
      isl_union_map_from_map(isl_map_copy(reads)));
  access = isl_union_access_info_set_must_source(
      access, isl_union_map_from_map(isl_map_copy(writes)));
  access = isl_union_access_info_set_schedule(
      access, isl_schedule_copy(scop->schedule));
  flow = isl_union_access_info_compute_flow(isl_union_access_info_copy(access));

  printf("\n");
  printf("access: %s\n", isl_union_access_info_to_str(access));
  printf("\n");
  printf("flow: %s\n", isl_union_flow_to_str(flow));

  may_dep = isl_union_flow_get_may_dependence(flow);
  printf("may_dep: %s\n", isl_union_map_to_str(may_dep));

  map = isl_union_map_as_map(isl_union_map_copy(schedule_map));
  bml = isl_map_get_basic_map_list(map);
  mat = isl_basic_map_equalities_matrix(isl_basic_map_list_get_at(bml, 0),
                                        isl_dim_in, isl_dim_out, isl_dim_cst,
                                        isl_dim_div, isl_dim_param);

  printf("MAT:\n");
  for (int i = 0; i < isl_mat_rows(mat); ++i) {
    for (int j = 0; j < isl_mat_cols(mat); ++j) {
      printf("%s ", isl_val_to_str(isl_mat_get_element_val(mat, i, j)));
    }
    printf("\n");
  }
  isl_map_free(map);
  isl_map_free(reads);
  isl_map_free(writes);
  isl_map_free(one);
  isl_union_set_free(domain);
  isl_union_map_free(schedule_map);
  isl_union_map_free(may_dep);
  isl_union_flow_free(flow);
  isl_union_access_info_free(access);
  isl_space_free(space);
  isl_set_free(set);
  return;
}

int main(int argc, char *argv[]) {
  struct options *options = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);
  const char *fn = argc > 1 ? argv[1] : filename;
  printf("Parsing: %s\n", fn);
  pet_scop *scop = pet_scop_extract_from_C_source(ctx, fn, "f");
  if (!scop) {
    printf("No scop found!\n");
    isl_ctx_free(ctx);
    return -1;
  }

  depanalysis(scop);

  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("DONE!\n");
}
