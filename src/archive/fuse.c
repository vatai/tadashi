
#include <isl/ast_build.h>
#include <stdio.h>

#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <pet.h>

#include "transformations.h"

static __isl_give isl_printer *scop_callback(__isl_take isl_printer *p,
                                             pet_scop *scop, void *user);

int main(int argc, char *argv[]) {

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  char input[] = "./tests/py/fuse_partial.c";
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
  node = tadashi_complete_fuse(node);

  isl_ctx *ctx = isl_schedule_get_ctx(sched);
  isl_ast_build *build = isl_ast_build_alloc(ctx);
  isl_ast_node *ast_node = isl_ast_build_node_from_schedule(build, sched);
  isl_ast_print_options *print_options = isl_ast_print_options_alloc(ctx);
  p = isl_ast_node_print(ast_node, p, print_options);
  isl_ast_build_free(build);
  pet_scop_free(scop);
  return p;
}
