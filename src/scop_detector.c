#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <pet.h>

#include "legality.h"

isl_printer *
transform(isl_printer *p, pet_scop *scop, void *user) {
  size_t *num_scops = user;
  struct tadashi_scop *ts = allocate_tadashi_scop(scop);
  isl_schedule_node *root = isl_schedule_get_root(ts->schedule);
  printf("scop[%d]:\n%s\n", *num_scops, isl_schedule_node_to_str(root));
  (*num_scops)++;
  return p;
}

int
main(int argc, char *argv[]) {
  char *input = argv[1];
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("/dev/null", "w");
  size_t num_scops = 0;
  pet_options_set_autodetect(ctx, 1);
  if (argc > 2 && strncmp(argv[2], "-a", 3) == 0) {
    printf("Disabling auto detection\n");
    pet_options_set_autodetect(ctx, 0);
  }
  pet_transform_C_source(ctx, input, output, transform, &num_scops);
  if (num_scops)
    printf("Number of scops in %s: %d\n", input, num_scops);
  return !num_scops;
}
