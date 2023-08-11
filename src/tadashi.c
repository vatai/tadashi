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

#include <stdio.h>
#include <stdlib.h>

#include <isl/arg.h>
#include <isl/ctx.h>
#include <isl/flow.h>
#include <isl/id.h>
#include <isl/id_to_id.h>
#include <isl/map.h>
#include <isl/options.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/union_set.h>
#include <isl/val.h>
#include <pet.h>

struct options {
  struct isl_options *isl;
  struct pet_options *pet;
  char *source_file;
  char *schedule;
  // unsigned tree;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, source_file, "source file", NULL)
ISL_ARG_STR(struct options, schedule, 's', "schedule", "schedule", NULL,
            "schedule")
ISL_ARGS_END
ISL_ARG_DEF(options, struct options, options_args)

/* Call "fn" on each declared array in "scop" that has an exposed field
 * equal to "exposed".
 */
static void foreach_declared_array(struct pet_scop *scop, int exposed,
                                   void (*fn)(struct pet_array *array,
                                              void *user),
                                   void *user) {
  int i;

  for (i = 0; i < scop->n_array; ++i) {
    struct pet_array *array = scop->arrays[i];

    if (array->declared && array->exposed == exposed)
      fn(array, user);
  }
}

/* foreach_declared_array callback that sets "indent"
 */
static void set_indent(struct pet_array *array, void *user) {
  int *indent = user;

  *indent = 1;
}

/* Internal data structure for print_array().
 * "p" is the printer to print on.
 * "build" is the build for building expressions.
 */
struct print_array_data {
  isl_printer *p;
  isl_ast_build *build;
};

/* Print a declaration for "array' to data->p.
 *
 * The size of the array is obtained from the extent.
 * In particular, it is one more than the largest value
 * in every dimension.
 * Use data->build to build an AST expression for this size.
 * Just in case this AST expression contains any macro calls,
 * print all the corresponding macro definitions before printing
 * the actual declaration.
 */
static void print_array(struct pet_array *array, void *user) {
  struct print_array_data *data = user;
  isl_val *one;
  isl_multi_pw_aff *size;
  isl_ast_expr *expr;

  one = isl_val_one(isl_set_get_ctx(array->extent));
  size = isl_set_max_multi_pw_aff(isl_set_copy(array->extent));
  size = isl_multi_pw_aff_add_constant_val(size, one);
  expr = isl_ast_build_access_from_multi_pw_aff(data->build, size);
  data->p = isl_ast_expr_print_macros(expr, data->p);
  data->p = isl_printer_start_line(data->p);
  data->p = isl_printer_print_str(data->p, array->element_type);
  data->p = isl_printer_print_str(data->p, " ");
  data->p = isl_printer_print_ast_expr(data->p, expr);
  data->p = isl_printer_print_str(data->p, ";");
  data->p = isl_printer_end_line(data->p);
  isl_ast_expr_free(expr);
}

/* Print "str" to "p" on a separate line.
 */
static __isl_give isl_printer *print_str_on_line(__isl_take isl_printer *p,
                                                 const char *str) {
  p = isl_printer_start_line(p);
  p = isl_printer_print_str(p, str);
  p = isl_printer_end_line(p);

  return p;
}

/* Print declarations for all declared arrays, putting the hidden (non-exposed)
 * ones in a separate scope.  Set "indent" if there are any such arrays and
 * therefore a separate scope was created.
 */
static __isl_give isl_printer *
print_declarations(__isl_take isl_printer *p, __isl_keep isl_ast_build *build,
                   struct pet_scop *scop, int *indent) {
  struct print_array_data data = {.p = p, .build = build};
  int i;

  *indent = 0;

  foreach_declared_array(scop, 0, &set_indent, indent);

  foreach_declared_array(scop, 1, &print_array, &data);

  if (*indent) {
    p = print_str_on_line(p, "{");
    p = isl_printer_indent(p, 2);

    foreach_declared_array(scop, 0, &print_array, &data);
  }

  return p;
}

/* Close the scope created by print_declarations() if any,
 * i.e., if "indent" is set.
 */
static __isl_give isl_printer *print_end_declarations(__isl_take isl_printer *p,
                                                      int indent) {
  if (indent) {
    p = isl_printer_indent(p, -2);
    p = print_str_on_line(p, "}");
  }

  return p;
}

/* Set up a mapping from statement names to the corresponding statements.
 * Each statement is attached as a user pointer to an identifier
 * with the same name as the statement.
 */
static __isl_give isl_id_to_id *set_up_id2stmt(struct pet_scop *scop) {
  int i;
  isl_ctx *ctx;
  isl_id_to_id *id2stmt;

  ctx = isl_set_get_ctx(scop->context);
  id2stmt = isl_id_to_id_alloc(ctx, scop->n_stmt);

  for (i = 0; i < scop->n_stmt; ++i) {
    struct pet_stmt *stmt = scop->stmts[i];
    isl_id *tuple_id, *id;
    const char *name;

    tuple_id = isl_set_get_tuple_id(stmt->domain);
    name = isl_id_get_name(tuple_id);
    id = isl_id_alloc(ctx, name, stmt);
    id2stmt = isl_id_to_id_set(id2stmt, tuple_id, id);
  }

  return id2stmt;
}

/* Return the pet_stmt corresponding to "node", assuming it is a user node
 * in an AST generated by isl_ast_build_node_from_schedule and
 * looking up such statements in "id2stmt".
 *
 * A user node in an AST generated by isl_ast_build_node_from_schedule
 * performs a call to the statement.  That is, the statement name
 * is the first argument of the associated call expression.
 *
 * Extract this statement name and then look it up in "id2stmt".
 */
static struct pet_stmt *node_stmt(__isl_keep isl_ast_node *node,
                                  isl_id_to_id *id2stmt) {
  isl_ast_expr *expr, *arg;
  isl_id *id;
  struct pet_stmt *stmt;

  expr = isl_ast_node_user_get_expr(node);
  arg = isl_ast_expr_get_op_arg(expr, 0);
  isl_ast_expr_free(expr);
  id = isl_ast_expr_get_id(arg);
  isl_ast_expr_free(arg);

  id = isl_id_to_id_get(id2stmt, id);
  stmt = isl_id_get_user(id);
  isl_id_free(id);

  return stmt;
}

/* pet_stmt_build_ast_exprs callback for transforming
 * the index expression "index" of the reference with identifier "ref_id".
 *
 * In particular, pullback "index" over the function in "user".
 */
static __isl_give isl_multi_pw_aff *
pullback_index(__isl_take isl_multi_pw_aff *index, __isl_keep isl_id *ref_id,
               void *user) {
  isl_pw_multi_aff *fn = user;

  fn = isl_pw_multi_aff_copy(fn);
  return isl_multi_pw_aff_pullback_pw_multi_aff(index, fn);
}

/* isl_id_set_free_user callback for freeing
 * a user pointer of type isl_id_to_ast_expr.
 */
static void free_isl_id_to_ast_expr(void *user) {
  isl_id_to_ast_expr *id_to_ast_expr = user;

  isl_id_to_ast_expr_free(id_to_ast_expr);
}

/* This callback is called on each leaf node of the AST generated
 * by isl_ast_build_node_from_schedule.
 * "node" is the generated leaf node.
 * "build" is the build within which the leaf node is generated.
 *
 * Obtain the schedule at the point where the leaf node is generated.
 * This is known to apply to a single statement, the one for which
 * the leaf node is being generated.
 * It is also known to map statement instances to unique elements
 * in the target space.  This means the inverse mapping is single-valued and
 * can be converted to a function.  Use this function to reformulate
 * all index expressions to refer to the schedule dimensions
 * when generating AST expressions for all accesses
 * in pet_stmt_build_ast_exprs.
 *
 * Attach the generated AST expressions, keyed off the corresponding
 * reference identifiers, to the AST node as an annotation.
 * This annotation will be retrieved in peek_ref2expr().
 */
static __isl_give isl_ast_node *at_domain(__isl_take isl_ast_node *node,
                                          __isl_keep isl_ast_build *build,
                                          void *user) {
  isl_id_to_id *id2stmt = user;
  isl_id *id;
  struct pet_stmt *stmt;
  isl_map *schedule;
  isl_pw_multi_aff *reverse;
  isl_id_to_ast_expr *ref2expr;

  stmt = node_stmt(node, id2stmt);

  schedule = isl_map_from_union_map(isl_ast_build_get_schedule(build));
  reverse = isl_pw_multi_aff_from_map(isl_map_reverse(schedule));
  ref2expr = pet_stmt_build_ast_exprs(stmt, build, &pullback_index, reverse,
                                      NULL, NULL);
  isl_pw_multi_aff_free(reverse);

  id = isl_id_alloc(isl_ast_node_get_ctx(node), NULL, ref2expr);
  id = isl_id_set_free_user(id, &free_isl_id_to_ast_expr);
  node = isl_ast_node_set_annotation(node, id);
  return node;
}

/* Return the generated AST expressions, keyed off the corresponding
 * reference identifiers, that were attached to "node"
 * as an annotation in at_domain().
 */
static __isl_keep isl_id_to_ast_expr *
peek_ref2expr(__isl_keep isl_ast_node *node) {
  isl_id *id;
  isl_id_to_ast_expr *ref2expr;

  id = isl_ast_node_get_annotation(node);
  ref2expr = isl_id_get_user(id);
  isl_id_free(id);

  return ref2expr;
}

/* isl_id_to_ast_expr_foreach callback that prints the definitions of the macros
 * called by "expr".
 */
static isl_stat expr_print_macros(__isl_take isl_id *id,
                                  __isl_take isl_ast_expr *expr, void *user) {
  isl_printer **p = user;

  *p = isl_ast_expr_print_macros(expr, *p);

  isl_id_free(id);
  isl_ast_expr_free(expr);

  return isl_stat_non_null(*p);
}

/* If "node" is a user node, then print the definitions of the macros
 * that get called in the AST expressions attached to the node.
 */
static isl_bool node_print_macros(__isl_keep isl_ast_node *node, void *user) {
  isl_id_to_ast_expr *ref2expr;

  if (isl_ast_node_get_type(node) != isl_ast_node_user)
    return isl_bool_true;

  ref2expr = peek_ref2expr(node);
  if (isl_id_to_ast_expr_foreach(ref2expr, &expr_print_macros, user) < 0)
    return isl_bool_error;

  return isl_bool_false;
}

/* Print the definitions of the macros that get called by "node".
 * This includes any macros that get called in the AST expressions
 * attached to the user nodes.
 */
static __isl_give isl_printer *print_macros(__isl_take isl_printer *p,
                                            __isl_keep isl_ast_node *node) {
  if (isl_ast_node_foreach_descendant_top_down(node, &node_print_macros, &p) <
      0)
    return isl_printer_free(p);
  p = isl_ast_node_print_macros(node, p);
  return p;
}

/* Print the body of the statement corresponding to user node "node" to "p".
 */
static __isl_give isl_printer *
print_user(__isl_take isl_printer *p, __isl_take isl_ast_print_options *options,
           __isl_keep isl_ast_node *node, void *user) {
  isl_id_to_id *id2stmt = user;
  struct pet_stmt *stmt;
  isl_id_to_ast_expr *ref2expr;

  stmt = node_stmt(node, id2stmt);
  ref2expr = peek_ref2expr(node);

  p = pet_stmt_print_body(stmt, p, ref2expr);

  isl_ast_print_options_free(options);

  return p;
}

/*
 * Modifications by Emil VATAI, Riken, R-CCS, HPAIS. All rights
 * reserved.  Date: 2023-08-04
 */

#define MAX_PATH_LEN 1024
struct transform_args {
  char *input_source_file;
  char output_file_name[MAX_PATH_LEN];
  size_t counter;
  isl_union_map *dependencies;
};

void update_filename(struct transform_args *args) {
  int rv;
  rv = sprintf(args->output_file_name, "%s.%lu.yaml", args->input_source_file,
               args->counter);
  if (rv < 0 || rv >= MAX_PATH_LEN) {
    fprintf(stderr, "UserError: source file (path) is too long!\n");
    exit(2);
  }
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
static __isl_give isl_printer *
dump_schedules(__isl_take isl_printer *p, struct pet_scop *scop, void *user) {
  isl_ctx *ctx;
  isl_schedule *schedule;
  isl_schedule_node *node;
  FILE *file;
  isl_printer *fp;
  struct transform_args *args;

  args = user;
  if (!scop || !p)
    return isl_printer_free(p);
  ctx = isl_printer_get_ctx(p);

  update_filename(args);
  file = fopen(args->output_file_name, "w");
  fp = isl_printer_to_file(ctx, file);

  node = isl_schedule_get_root(scop->schedule);
  fp = isl_printer_print_schedule_node(fp, node);
  printf("Written: %s\n", args->output_file_name);

  isl_printer_free(fp);
  fclose(file);
  isl_schedule_node_free(node);
  pet_scop_free(scop);

  ++(args->counter);
  return p;
}

__isl_give isl_union_flow *get_flow_from_scop(__isl_keep pet_scop *scop) {
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

__isl_give isl_union_map *get_dependencies(pet_scop *scop) {
  isl_union_map *dep;
  isl_union_flow *flow;
  flow = get_flow_from_scop(scop);
  dep = isl_union_flow_get_may_dependence(flow);
  isl_union_flow_free(flow);
  return dep;
}

__isl_give isl_union_set *
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

  domain = isl_union_map_apply_domain(dep, isl_union_map_copy(schedule_map));
  domain = isl_union_map_apply_range(domain, schedule_map);
  delta = isl_union_map_deltas(domain);

  zeros = get_zeros_on_union_set(isl_union_set_copy(delta));

  le = isl_union_set_lex_le_union_set(delta, zeros);
  isl_bool retval = isl_union_map_is_empty(le);
  isl_union_map_free(le);
  return retval;
}

isl_bool check_schedule_legality(isl_ctx *ctx, isl_schedule *schedule,
                                 __isl_take isl_union_map *dep) {
  return check_legality(ctx, isl_schedule_get_map(schedule), dep);
}

/* NEED TO REWRITE THIS This function is called for each each scop
 * detected in the input file and is expected to write (a transformed
 * version of) the scop "scop" to the printer "p".  "user" is the
 * value passed to pet_transform_C_source.
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
static __isl_give isl_printer *transform(__isl_take isl_printer *p,
                                         struct pet_scop *scop, void *user) {
  int indent;
  isl_ctx *ctx;
  isl_schedule *schedule;
  isl_ast_build *build;
  isl_ast_node *node;
  isl_ast_print_options *print_options;
  isl_id_to_id *id2stmt;
  char buffer[80];
  struct transform_args *yaml_struct = user;

  if (!scop || !p)
    return isl_printer_free(p);

  ctx = isl_printer_get_ctx(p);
  schedule = isl_schedule_copy(scop->schedule);
  id2stmt = set_up_id2stmt(scop);
  build = isl_ast_build_alloc(ctx);
  build = isl_ast_build_set_at_each_domain(build, &at_domain, id2stmt);
  node = isl_ast_build_node_from_schedule(build, schedule);
  print_options = isl_ast_print_options_alloc(ctx);
  print_options =
      isl_ast_print_options_set_print_user(print_options, &print_user, id2stmt);

  sprintf(buffer, "// !!! BEGIN SCOP %d !!!", yaml_struct->counter);
  p = print_str_on_line(p, buffer);
  p = print_declarations(p, build, scop, &indent);
  p = print_macros(p, node);
  p = isl_ast_node_print(node, p, print_options);
  p = print_end_declarations(p, indent);
  sprintf(buffer, "// !!! END SCOP %d !!!", yaml_struct->counter);
  p = print_str_on_line(p, buffer);

  ++(yaml_struct->counter);

  isl_ast_node_free(node);
  isl_ast_build_free(build);
  isl_id_to_id_free(id2stmt);
  pet_scop_free(scop);

  return p;
}

int main(int argc, char *argv[]) {
  isl_ctx *ctx;
  struct options *opt;
  int r;

  opt = options_new_with_defaults();
  ctx = isl_ctx_alloc_with_options(&options_args, opt);
  argc = options_parse(opt, argc, argv, ISL_ARG_ALL);

  isl_options_set_ast_print_macro_once(ctx, 1);
  pet_options_set_encapsulate_dynamic_control(ctx, 1);
  pet_options_set_autodetect(ctx, 1);

  if (!opt->source_file) {
    fprintf(
        stderr,
        "UserError: Source file not specified (see %s --help for details)\n",
        argv[0]);
    return 1;
  }

  // if (!opt->schedule)
  // r = generate_yaml_files_with_original_schedules(ctx, opt->source_file);
  // else
  // r = apply_transformations_in_yaml_fils(ctx, opt->source_file);

  struct transform_args yaml_struct = {.counter = 0,
                                       .input_source_file = opt->source_file};
  FILE *dev_null = fopen("/dev/null", "w");
  r = pet_transform_C_source(ctx, opt->source_file, dev_null, &dump_schedules,
                             &yaml_struct);
  fclose(dev_null);
  printf("Number of scops: %d\n", yaml_struct.counter);
  isl_ctx_free(ctx);
  printf("%s Done\n", argv[0]);
  return r;
}
