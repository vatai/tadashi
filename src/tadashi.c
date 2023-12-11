/*
 * Copyright 2023 Emil Vatai, Riken, R-CCS, HPAIS. All rights
 * reservered.
 *
 * Date: 2023-08-04
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

#include <isl/arg.h>
#include <stdio.h>
#include <string.h>

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
  char *original_schedule_suffix;
  char *dependencies_suffix;
  isl_bool legality_check;
  isl_bool interactive;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, "pet", &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, source_file_path, "source file", NULL)
ISL_ARG_STR(struct options, output_file_path, 'o', "output-file", "path",
            "out.c", "Output file")
ISL_ARG_STR(struct options, original_schedule_suffix, 's', "schedule-suffix",
            "suffix", "", "Original schedule file suffix")
ISL_ARG_STR(struct options, dependencies_suffix, 'd', "dependencies-suffix",
            "suffix", "", "Dependencies file suffix")
ISL_ARG_BOOL(struct options, legality_check, 0, "legality-check", isl_bool_true,
             "Check legality")
ISL_ARG_BOOL(struct options, interactive, 0, "interactive", isl_bool_false,
             "Interactive transformations")
ISL_ARGS_END ISL_ARG_DEF(options, struct options, options_args);

struct user_t {
  size_t counter;
  struct options *opt;
};

void print_schedule(isl_ctx *ctx, __isl_keep isl_schedule *schedule,
                    size_t counter) {
  isl_schedule_node *root;
  root = isl_schedule_get_root(schedule);
  printf("### sched[%lu] begin ###\n", counter);
  isl_schedule_dump(schedule);
  printf("### sched[%lu] end ###\n", counter);
  isl_schedule_node_free(root);
}

__isl_give isl_printer *new_printer(isl_ctx *ctx, const char *path,
                                    size_t count, const char *suffix) {
  FILE *file;
  size_t path_len = strnlen(path, 1024);
  size_t suffix_len = strnlen(suffix, 1024);
  if (suffix_len) {
    char *filename = malloc(path_len + suffix_len + 2); // + 2 = dot and \0
    sprintf(filename, "%s.%lu.%s", path, count, suffix);
    file = fopen(filename, "w");
    free(filename);
  } else {
    file = stdout;
  }
  return isl_printer_to_file(ctx, file);
}

void delete_printer(__isl_take isl_printer *p) {
  FILE *file = isl_printer_get_file(p);
  isl_printer_free(p);
  if (file != stdout)
    fclose(file);
}

__isl_give isl_printer *transform_scop(isl_ctx *ctx, __isl_take isl_printer *p,
                                       __isl_keep struct pet_scop *scop,
                                       struct user_t *user) {
  isl_schedule *schedule;
  isl_union_map *dependencies;
  isl_printer *tmp;
  isl_bool legal;
  if (user->opt->legality_check)
    printf("\n>>> CHECK LEGALITY <<<\n");
  else
    printf("\n<<< DON'T CHECK LEGALITY >>>\n");
  dependencies = get_dependencies(scop);
  printf("\nPrinting dependencies...\n");
  tmp = new_printer(ctx, user->opt->source_file_path, user->counter,
                    user->opt->dependencies_suffix);
  tmp = isl_printer_print_union_map(tmp, dependencies);
  delete_printer(tmp);
  printf("\n");

  if (user->opt->legality_check) {
    schedule = isl_schedule_read_from_file(ctx, stdin);
    legal = check_schedule_legality(ctx, schedule, dependencies);
    if (!legal) {
      printf("Illegal schedule!\n");
      isl_schedule_free(schedule);
      schedule = pet_scop_get_schedule(scop);
    } else {
      printf("Schedule is legal!\n");
    };
  } else {
    printf("Schedule not checked!\n");
    isl_union_map_free(dependencies);
    schedule = pet_scop_get_schedule(scop);
  }
  p = generate_code(ctx, p, scop, schedule);
  return p;
}

/*
 * IGNORE THIS COMMENT, IT'S FROM THE OLD CODE:
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
                                                     void *_user) {
  isl_ctx *ctx;
  struct user_t *user = _user;
  isl_printer *tmp;

  printf("Begin processing SCOP %lu\n", user->counter);
  if (!scop || !p)
    return isl_printer_free(p);
  ctx = isl_printer_get_ctx(p);

  print_schedule(ctx, scop->schedule, user->counter);

  tmp = new_printer(ctx, user->opt->source_file_path, user->counter,
                    user->opt->original_schedule_suffix);
  tmp = isl_printer_print_schedule(tmp, scop->schedule);
  delete_printer(tmp);
  printf("\n");

  p = transform_scop(ctx, p, scop, user);
  pet_scop_free(scop);
  printf("End processing SCOP %lu\n", user->counter);
  user->counter++;
  return p;
}

int main(int argc, char *argv[]) {
  int r;
  isl_ctx *ctx;
  struct user_t user;
  user.counter = 0;

  printf("WARNING: This app should only be invoked by the python wrapper!\n");
  user.opt = options_new_with_defaults();
  argc = options_parse(user.opt, argc, argv, ISL_ARG_ALL);
  ctx = isl_ctx_alloc_with_options(&options_args, user.opt);

  isl_options_set_ast_print_macro_once(ctx, 1);
  pet_options_set_encapsulate_dynamic_control(ctx, 1);

  FILE *output_file = fopen(user.opt->output_file_path, "w");
  r = pet_transform_C_source(ctx, user.opt->source_file_path, output_file,
                             &foreach_scop_callback, &user);
  fprintf(stderr, "Number of scops: %lu\n", user.counter);
  fclose(output_file);
  isl_ctx_free(ctx);
  printf("### STOP ###\n");
  return r;
}
