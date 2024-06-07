
#include <stdio.h>

#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <pet.h>

#include "codegen.h"
#include "legality.h"
#include "transformations.h"

static __isl_give isl_printer *scop_callback(__isl_take isl_printer *p,
                                             pet_scop *scop, void *user);

static int generate_code(const char *input_path, const char *output_path,
                         isl_ctx *ctx);

static __isl_give isl_printer *generate_code_callback(__isl_take isl_printer *p,
                                                      struct pet_scop *scop,
                                                      void *user);
int main(int argc, char *argv[]) {

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  char input[] = "./tests/py/test_fuse.c";
  FILE *output = fopen("cout.c", "w");
  // pet_options_set_autodetect(ctx, 1);
  pet_transform_C_source(ctx, input, output, scop_callback, NULL);
  fclose(output);
  return 0;
}

static __isl_give isl_printer *scop_callback(__isl_take isl_printer *p,
                                             pet_scop *scop, void *user) {
  if (!scop || !p)
    return isl_printer_free(p);
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(sched);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  node = tadashi_fuse(node, 0, 1);
  // isl_union_map *dep = get_dependencies(scop);
  p = codegen(p, scop, sched);
  pet_scop_free(scop);
  return p;
}
