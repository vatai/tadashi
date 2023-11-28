/*
 * Copyright 2023  Emil Vatai. All rights reservered.
 *
 * The main program. For each scop in a C source file:
 *
 * + Read the original schedules using pet, and print it in yaml
 *   format to `stdout`.
 *
 * + Transform the SCoP:
 *
 *   1. Read a schedule (in yaml format) from `stdin`,
 *
 *   2. Check legality, and
 *
 *   3. Generate a C code according to the new schedule if it is legal
 *   or according to the original schedule otherwise.
 *
 */

#include <stdio.h>

#include <isl/ctx.h>
#include <isl/options.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/union_map.h>

#include <pet.h>

#include "codegen.h"
#include "legality.h"

struct options {
  struct isl *isl;
  struct pet *pet;
  char *source_file_path;
  char *output_file_path;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, "pet", &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, source_file_path, "source file", NULL)
ISL_ARG_STR(struct options, output_file_path, 'o', NULL, "output file", "out.c",
            "Output file")
ISL_ARGS_END ISL_ARG_DEF(options, struct options, options_args);

/*
 * Modifications by Emil VATAI, Riken, R-CCS, HPAIS. All rights
 * reserved.  Date: 2023-08-04
 */

void print_schedule(isl_ctx *ctx, __isl_keep isl_schedule *schedule,
                    size_t *counter) {
  isl_schedule_node *root;
  root = isl_schedule_get_root(schedule);
  printf("### sched[%lu] begin ###\n", *counter);
  isl_schedule_dump(schedule);
  printf("### sched[%lu] end ###\n", *counter);
  isl_schedule_node_free(root);
}

__isl_give isl_printer *transform_scop(isl_ctx *ctx, __isl_take isl_printer *p,
                                       __isl_keep struct pet_scop *scop) {
  isl_schedule *schedule;
  isl_union_map *dependencies;
  schedule = isl_schedule_read_from_file(ctx, stdin);
  isl_schedule_dump(schedule);
  dependencies = get_dependencies(scop);
  isl_union_map_dump(dependencies);
  isl_bool legal = check_schedule_legality(ctx, schedule, dependencies);
  if (!legal) {
    printf("Illegal schedule!\n");
    isl_schedule_free(schedule);
    schedule = pet_scop_get_schedule(scop);
  } else {
    printf("Schedule is legal!\n");
  }
  p = generate_code(ctx, p, scop, schedule);
  return p;
}

/* IGNORE THIS COMMENT, IT'S FROM THE OLD CODE:
 *
 * This function is called for each each scop detected
 * in the input file and is expected to write (a transformed version of) the
 * scop "scop" to the printer "p". "user" is the value passed to
 * pet_transform_C_source.
 *
 * This particular callback does not perform any transformation and
 * simply prints out the original scop.
 * "user" is set to NULL.
 *
 * First build a map from statement names to the corresponding statements.
 * This will be used to recover the statements from their names
 * in at_domain() and print_user().
 *
 * Then create an isl_ast_build that will be used to build all AST nodes and
 * expressions.  Set a callback that will be called
 * by isl_ast_build_node_from_schedule for each leaf node.
 * This callback takes care of creating AST expressions
 * for all accesses in the corresponding statement and attaches
 * them to the node.
 *
 * Generate an AST using the original schedule and print it
 * using print_user() for printing statement bodies.
 *
 * Before printing the AST itself, print out the declarations
 * of any variables that are declared inside the scop, as well as
 * the definitions of any macros that are used in the generated AST or
 * any of the generated AST expressions.
 * Finally, close any scope that may have been opened
 * to print variable declarations.
 */
static __isl_give isl_printer *foreach_scop_callback(__isl_take isl_printer *p,
                                                     struct pet_scop *scop,
                                                     void *user) {
  isl_ctx *ctx;
  isl_schedule *schedule;
  size_t *counter = user;
  FILE *input_schedule_file;

  printf("Begin processing SCOP %lu\n", *counter);
  if (!scop || !p)
    return isl_printer_free(p);
  ctx = isl_printer_get_ctx(p);

  print_schedule(ctx, scop->schedule, counter);
  p = transform_scop(ctx, p, scop);
  pet_scop_free(scop);
  printf("End processing SCOP %lu\n", *counter);
  ++(*counter);
  return p;
}

int main(int argc, char *argv[]) {
  int r;
  isl_ctx *ctx;
  struct options *opt;
  size_t counter = 0;

  printf("WARNING: This app should only be invoked by the python wrapper!\n");
  opt = options_new_with_defaults();
  argc = options_parse(opt, argc, argv, ISL_ARG_ALL);
  ctx = isl_ctx_alloc_with_options(&options_args, opt);

  isl_options_set_ast_print_macro_once(ctx, 1);
  pet_options_set_encapsulate_dynamic_control(ctx, 1);

  FILE *output_file = fopen(opt->output_file_path, "w");
  r = pet_transform_C_source(ctx, opt->source_file_path, output_file,
                             &foreach_scop_callback, &counter);
  fprintf(stderr, "Number of scops: %lu\n", counter);
  fclose(output_file);
  isl_ctx_free(ctx);
  printf("### STOP ###\n");
  return r;
}
