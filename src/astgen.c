#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <stdio.h>

#include <isl/ctx.h>
#include <isl/options.h>
#include <pet.h>

int main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();
  pet_scop *scop =
      pet_scop_extract_from_C_source(ctx, "../examples/depnodep.cc", 0);
  isl_schedule *schedule = pet_scop_get_schedule(scop);
  isl_schedule_node *root = isl_schedule_get_root(schedule);
  printf("root: %s\n", isl_schedule_node_to_str(root));

  return 0;
}
