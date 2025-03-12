#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <stddef.h>
#include <stdio.h>

#include <isl/ctx.h>
#include <pet.h>

isl_printer *
transform(isl_printer *p, pet_scop *scop, void *user) {
  size_t *num_scops = user;
  isl_schedule *schedule = pet_scop_get_schedule(scop);
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  printf("scop[%d]:\n%s\n", num_scops, isl_schedule_node_to_str(root));
  (*num_scops)++;
  return p;
}

int
main(int argc, char *argv[]) {
  char *input = argv[1];
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("/dev/null", "w");
  size_t num_scops = 0;
  pet_transform_C_source(ctx, input, output, transform, &num_scops);
  printf("Number of scops detected: %d\n", num_scops);
  return 0;
}
