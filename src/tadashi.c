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

/*
 * Copyright 2022      Sven Verdoolaege. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *    1. Redistributions of source code must retain the above
 *       copyright notice, this list of conditions and the following
 *       disclaimer.
 *
 *    2. Redistributions in binary form must reproduce the above
 *       copyright notice, this list of conditions and the following
 *       disclaimer in the documentation and/or other materials
 *       provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY SVEN VERDOOLAEGE ''AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SVEN VERDOOLAEGE OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
 * USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * The views and conclusions contained in the software and
 * documentation are those of the authors and should not be
 * interpreted as representing official policies, either expressed or
 * implied, of Sven Verdoolaege.
 */

/*
 * Modifications by Emil VATAI, Riken, R-CCS, HPAIS. All rights
 * reserved.  Date: 2023-08-04
 */

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <pet.h>

#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/arg.h>
#include <isl/ast.h>
#include <isl/ast_build.h>
#include <isl/ast_type.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/id.h>
#include <isl/id_to_id.h>
#include <isl/map.h>
#include <isl/options.h>
#include <isl/printer.h>
#include <isl/printer_type.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/space_type.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

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

static __isl_give isl_union_flow *
get_flow_from_scop(__isl_keep pet_scop *scop) {
  isl_union_map *sink, *may_source, *must_source;
  isl_union_access_info *access;
  isl_schedule *schedule;
  isl_union_flow *flow;
  sink = pet_scop_get_may_reads(scop);
  access = isl_union_access_info_from_sink(sink);

  may_source = pet_scop_get_may_writes(scop);
  access = isl_union_access_info_set_may_source(access, may_source);

  must_source = pet_scop_get_must_writes(scop);
  access = isl_union_access_info_set_must_source(access, must_source);

  schedule = pet_scop_get_schedule(scop);
  access = isl_union_access_info_set_schedule(access, schedule);

  flow = isl_union_access_info_compute_flow(access);
  return flow;
}

static __isl_give isl_union_map *
get_dependencies(__isl_keep struct pet_scop *scop) {
  isl_union_map *dep;
  isl_union_flow *flow;
  flow = get_flow_from_scop(scop);
  dep = isl_union_flow_get_may_dependence(flow);
  isl_union_flow_free(flow);
  return dep;
}

static __isl_give isl_union_set *
get_zeros_on_union_set(__isl_take isl_union_set *delta_uset) {
  isl_set *delta_set;
  isl_multi_aff *ma;

  delta_set = isl_set_from_union_set(delta_uset);
  ma = isl_multi_aff_zero(isl_set_get_space(delta_set));
  isl_set_free(delta_set);
  return isl_union_set_from_set(isl_set_from_multi_aff(ma));
}

isl_bool check_legality(isl_ctx *ctx, __isl_take isl_union_map *schedule_map,
                        __isl_take isl_union_map *dep) {
  isl_union_map *domain, *le;
  isl_union_set *delta, *zeros;

  if (isl_union_map_is_empty(dep)) {
    isl_union_map_free(dep);
    isl_union_map_free(schedule_map);
    return isl_bool_true;
  }
  domain = isl_union_map_apply_domain(dep, isl_union_map_copy(schedule_map));
  domain = isl_union_map_apply_range(domain, schedule_map);
  delta = isl_union_map_deltas(domain);
  zeros = get_zeros_on_union_set(isl_union_set_copy(delta));
  le = isl_union_set_lex_le_union_set(delta, zeros);
  isl_bool retval = isl_union_map_is_empty(le);
  isl_union_map_free(le);
  return retval;
}

isl_bool legality_test(__isl_keep isl_schedule_node *node, void *user) {
  enum isl_schedule_node_type type;
  isl_multi_union_pw_aff *mupa;
  isl_union_map *domain, *le;
  isl_union_set *delta, *zeros;
  isl_union_map *dep = user;
  type = isl_schedule_node_get_type(node);
  switch (type) {
  case isl_schedule_node_band:
    mupa = isl_schedule_node_band_get_partial_schedule(node);
    /* printf("MUPA %s\n", isl_multi_union_pw_aff_to_str(mupa)); */
    isl_union_map *partial = isl_union_map_from_multi_union_pw_aff(mupa);
    /* printf("      UMAP %s\n", isl_union_map_to_str(partial)); */
    /* printf("      DEP: %s\n", isl_union_map_to_str(dep)); */
    domain = isl_union_map_apply_domain(isl_union_map_copy(dep),
                                        isl_union_map_copy(partial));
    domain = isl_union_map_apply_range(domain, partial);
    /* printf("      DOM: %s\n", isl_union_map_to_str(domain)); */
    delta = isl_union_map_deltas(domain);
    /* printf("      DEL: %s\n", isl_union_set_to_str(delta)); */
    isl_union_set_foreach_set(delta, delta_set_lexpos, NULL);
    isl_union_set_free(delta);
    break;
  }

  return isl_bool_true;
}

isl_bool check_schedule_legality(isl_ctx *ctx,
                                 __isl_keep isl_schedule *schedule,
                                 __isl_take isl_union_map *dep) {
  isl_bool legal;
  isl_schedule_node *root;
  isl_union_pw_multi_aff *dep_upma;
  root = isl_schedule_get_root(schedule);
  // dep_upma = isl_union_pw_multi_aff_from_union_map(isl_union_map_copy(dep));
  legal = isl_schedule_node_every_descendant(root, legality_test, dep);
  // isl_union_pw_multi_aff_free(dep_upma);
  isl_schedule_node_free(root);
  isl_union_map *map = isl_schedule_get_map(schedule);
  printf("schedule as union map:\n%s\n", isl_union_map_to_str(map));
  return check_legality(ctx, map, dep);
}

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

/* NEED TO REWRITE THIS: This function is called for each each scop detected
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
