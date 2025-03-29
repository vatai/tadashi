#include <stdio.h>
#include <stdlib.h>

#include <pet.h>

#include <isl/schedule.h>
#include <isl/union_map.h>

isl_printer *
transform(isl_printer *p, pet_scop *scop, void *user) {
  // printf("Schedule: %s\n", isl_schedule_to_str(scop->schedule));
  isl_union_map *kills = pet_scop_get_must_kills(scop);
  printf("kills: %s\n", isl_union_map_to_str(kills));
  return p;
}

int
main(int argc, char *argv[]) {
  putenv(
      "C_INCLUDE_PATH=/home/vatai/code/tadashi/examples/polybench/utilities");
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("killer.out.c", "w");
  const char *input = "/home/vatai/code/tadashi/examples/polybench/"
                      "linear-algebra/blas/gemm/gemm.c";
  pet_transform_C_source(ctx, input, output, transform, NULL);
  printf("bye!\n");
  return 0;
}
