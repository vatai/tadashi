/** @file
 * @author Emil Vatai
 */
/*
 * Modifications and additions: Emil VATAI, Riken
 *
 * All rights reserved.  Date: 2023-08-04
 *
 * Many functions in this file are copied from or based on:
 * https://repo.or.cz/pet.git/blob/HEAD:/pet_loopback.c
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

#include <ctype.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <isl/ast.h>
#include <isl/ast_build.h>
#include <isl/id.h>
#include <isl/id_to_id.h>
#include <isl/printer.h>
#include <isl/schedule_node.h>
#include <isl/space.h>
#include <isl/union_set.h>
#include <isl/val.h>
#include <pet.h>

#include "codegen.h"

/* Call "fn" on each declared array in "scop" that has an exposed field
 * equal to "exposed".
 */
static void
foreach_declared_array(struct pet_scop *scop, int exposed,
                       void (*fn)(struct pet_array *array, void *user),
                       void *user) {
  int i;

  for (i = 0; i < scop->n_array; ++i) {
    struct pet_array *array = scop->arrays[i];

    if (array->declared && array->exposed == exposed)
      fn(array, user);
  }
}

/** foreach_declared_array callback that sets "indent"
 */
static void
set_indent(struct pet_array *array, void *user) {
  int *indent = user;

  *indent = 1;
}

/** Internal data structure for print_array().
 * `p` is the printer to print on.
 * `build` is the build for building expressions.
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
static void
print_array(struct pet_array *array, void *user) {
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
static __isl_give isl_printer *
print_str_on_line(__isl_take isl_printer *p, const char *str) {
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
static __isl_give isl_printer *
print_end_declarations(__isl_take isl_printer *p, int indent) {
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
static __isl_give isl_id_to_id *
set_up_id2stmt(struct pet_scop *scop) {
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
static struct pet_stmt *
node_stmt(__isl_keep isl_ast_node *node, isl_id_to_id *id2stmt) {
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
static void
free_isl_id_to_ast_expr(void *user) {
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
static __isl_give isl_ast_node *
at_domain(__isl_take isl_ast_node *node, __isl_keep isl_ast_build *build,
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
static isl_stat
expr_print_macros(__isl_take isl_id *id, __isl_take isl_ast_expr *expr,
                  void *user) {
  isl_printer **p = user;

  *p = isl_ast_expr_print_macros(expr, *p);

  isl_id_free(id);
  isl_ast_expr_free(expr);

  return isl_stat_non_null(*p);
}

/* If "node" is a user node, then print the definitions of the macros
 * that get called in the AST expressions attached to the node.
 */
static isl_bool
node_print_macros(__isl_keep isl_ast_node *node, void *user) {
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
static __isl_give isl_printer *
print_macros(__isl_take isl_printer *p, __isl_keep isl_ast_node *node) {
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

static int
get_num_threads_from_pragma_parallel(__isl_take isl_id *id) {
  const int failure = -1;
  if (!id)
    return failure;
  const char *id_name = isl_id_get_name(id);
  int num_threads;
  int rv = sscanf(id_name, "pragma_parallel_%d", &num_threads);
  isl_id_free(id);
  return rv == 1 ? num_threads : failure;
}

static __isl_give isl_printer *
print_for(__isl_take isl_printer *p, __isl_take isl_ast_print_options *options,
          __isl_keep isl_ast_node *for_node, void *user) {
  isl_ast_expr *iter = isl_ast_node_for_get_iterator(for_node);
  isl_ast_expr *init = isl_ast_node_for_get_init(for_node);
  isl_ast_expr *cond = isl_ast_node_for_get_cond(for_node);
  isl_ast_expr *inc = isl_ast_node_for_get_inc(for_node);
  isl_ast_node *body = isl_ast_node_for_get_body(for_node);

  isl_id *annotation = isl_ast_node_get_annotation(for_node);

  int num_threads = get_num_threads_from_pragma_parallel(annotation);
  if (num_threads != -1) {
    char pragma_line[LINE_MAX];
    if (num_threads)
      sprintf(pragma_line, "#pragma omp parallel for num_threads(%d)\n",
              num_threads);
    else
      sprintf(pragma_line, "#pragma omp parallel for\n");
    p = isl_printer_print_str(p, pragma_line);
  }

  p = isl_printer_start_line(p);
  p = isl_printer_indent(p, 2);
  p = isl_printer_print_str(p, "for(int ");
  p = isl_printer_print_ast_expr(p, iter);
  p = isl_printer_print_str(p, " = ");
  p = isl_printer_print_ast_expr(p, init);
  p = isl_printer_print_str(p, "; ");
  p = isl_printer_print_ast_expr(p, cond);
  p = isl_printer_print_str(p, "; ");
  p = isl_printer_print_ast_expr(p, iter);
  p = isl_printer_print_str(p, " += ");
  p = isl_printer_print_ast_expr(p, inc);
  p = isl_printer_print_str(p, ")");
  p = isl_printer_end_line(p);
  p = isl_ast_node_print(body, p, options);
  p = isl_printer_indent(p, -2);

  isl_ast_expr_free(iter);
  isl_ast_expr_free(init);
  isl_ast_expr_free(cond);
  isl_ast_expr_free(inc);
  isl_ast_node_free(body);
  return p;
}

__isl_give isl_ast_node *
after_mark(__isl_take isl_ast_node *mark_node, __isl_keep isl_ast_build *build,
           void *user) {
  isl_ctx *ctx = isl_ast_node_get_ctx(mark_node);
  isl_id *mark_id = isl_ast_node_mark_get_id(mark_node);

  const char *id_name = isl_id_get_name(mark_id);
  int starts_with_pragma = !strncmp(id_name, "pragma", 6);
  mark_id = isl_id_free(mark_id);
  if (!starts_with_pragma)
    return mark_node;

  isl_ast_node *for_node = isl_ast_node_mark_get_node(mark_node);
  isl_ast_node_free(mark_node);
  // Copy the name of the annotation id of the `mark_node` in the
  // schedule tree to the name of the annotation id of the `for_node`
  // in the AST, since the AST does not have access to the `mark_node`
  // from the schedule tree directly.
  isl_id *annotation = isl_id_alloc(ctx, id_name, NULL);
  for_node = isl_ast_node_set_annotation(for_node, annotation);
  return for_node;
}

/* isl_union_map_foreach_map callback: track max output dim across all maps. */
static isl_stat
_max_map_out_dim(__isl_take isl_map *map, void *user) {
  isl_size *max_dim = (isl_size *)user;
  isl_size d = isl_map_dim(map, isl_dim_out);
  if (d > *max_dim)
    *max_dim = d;
  isl_map_free(map);
  return isl_stat_ok;
}

/* Return the number of schedule dimensions required to name every loop level
 * in "schedule", i.e. the maximum output dimension of any per-statement map
 * in the schedule's union map. */
static size_t
_schedule_num_iterators(__isl_keep isl_schedule *schedule) {
  isl_union_map *umap = isl_schedule_get_map(schedule);
  isl_size max_dim = 0;
  isl_union_map_foreach_map(umap, _max_map_out_dim, &max_dim);
  isl_union_map_free(umap);
  return max_dim < 0 ? 0 : (size_t)max_dim;
}

/* The iterator names in the generated code are derived from the names of
 * the iteration domain dimensions, i.e. from the iterator names in the
 * original source.  pet stores those names in the statement spaces, which
 * no transformation renames, so they survive an arbitrary sequence of
 * transformations.  The code below turns them into the list of names passed
 * to isl_ast_build_set_iterators(), falling back to the depth based
 * `_tadashi_<depth>` names where an original name cannot be determined.
 *
 * `ITERATOR_BASE_SIZE` is the maximum length of the name a loop iterator is
 * named after; longer names get truncated.  `ITERATOR_NAME_SIZE` leaves
 * room for the disambiguating suffix described in _unique_name().
 */
#define ITERATOR_BASE_SIZE 40
#define ITERATOR_NAME_SIZE 64

/* A set of names.  Used both to collect the identifiers a generated loop
 * iterator must not shadow and to keep the names handed out unique.
 */
struct name_set {
  char **names;
  size_t n;
  size_t alloc;
};

/* Does "set" contain "name"?
 */
static int
name_set_has(const struct name_set *set, const char *name) {
  for (size_t i = 0; i < set->n; i++)
    if (!strcmp(set->names[i], name))
      return 1;
  return 0;
}

/* Add a copy of "name" to "set", unless it is NULL or already present.
 */
static void
name_set_add(struct name_set *set, const char *name) {
  char *copy;

  if (!name || name_set_has(set, name))
    return;
  if (set->n == set->alloc) {
    size_t alloc = set->alloc ? 2 * set->alloc : 16;
    char **names = realloc(set->names, alloc * sizeof(*names));

    if (!names)
      return;
    set->names = names;
    set->alloc = alloc;
  }
  copy = strdup(name);
  if (copy)
    set->names[set->n++] = copy;
}

static void
name_set_free(struct name_set *set) {
  for (size_t i = 0; i < set->n; i++)
    free(set->names[i]);
  free(set->names);
  set->names = NULL;
  set->n = set->alloc = 0;
}

/* pet_tree_foreach_access_expr callback adding the name of the array or
 * scalar accessed by "expr" to the name set in "user".
 *
 * Not every access expression refers to something by name (the index
 * expression of an access to an array of structures, for instance), and
 * pet_expr_access_get_id() warns about those, so check first.  A nameless
 * access cannot be shadowed anyway.
 */
static int
_add_accessed_name(__isl_keep pet_expr *expr, void *user) {
  isl_multi_pw_aff *index = pet_expr_access_get_index(expr);
  isl_space *space = isl_multi_pw_aff_get_space(index);
  isl_bool has_name = isl_space_has_tuple_name(space, isl_dim_out);

  isl_space_free(space);
  isl_multi_pw_aff_free(index);
  if (has_name == isl_bool_true) {
    isl_id *id = pet_expr_access_get_id(expr);

    name_set_add(user, isl_id_get_name(id));
    isl_id_free(id);
  }
  return 0;
}

/* pet_expr_foreach_call_expr callback adding the name of the function
 * called by "expr" to the name set in "user".
 */
static int
_add_called_name(__isl_keep pet_expr *expr, void *user) {
  name_set_add(user, pet_expr_call_get_name(expr));
  return 0;
}

/* pet_tree_foreach_expr callback adding the names of all functions called
 * from "expr" to the name set in "user".
 */
static int
_add_called_names(__isl_keep pet_expr *expr, void *user) {
  return pet_expr_foreach_call_expr(expr, &_add_called_name, user);
}

/* isl_union_set_foreach_set callback adding the tuple name of "set" to the
 * name set in "user".
 */
static isl_stat
_add_tuple_name(__isl_take isl_set *set, void *user) {
  name_set_add(user, isl_set_get_tuple_name(set));
  isl_set_free(set);
  return isl_stat_ok;
}

/* Collect the identifiers that a generated loop iterator must not shadow.
 *
 * print_for() declares the iterator in the for loop itself, so a name that
 * is also used by the code inside the loop would silently change what that
 * code refers to.  The names to avoid are the parameters of "scop" and the
 * arrays, scalars and functions referenced by its statements, plus the
 * macros isl may emit for the loop bounds.
 *
 * Only the statements that still appear in "schedule" are considered.  The
 * statements that were removed by dead code elimination are ignored on
 * purpose: when the original iterators are declared outside the scop (as in
 * an `int i, j, k;` in front of `#pragma scop`), pet models them as scalars
 * and the statements assigning them are exactly what dead code elimination
 * removes.  Nothing in the generated code refers to them anymore, so those
 * names are free to be reused, which is what this whole file is about.
 */
static void
collect_reserved_names(struct name_set *reserved,
                       __isl_keep struct pet_scop *scop,
                       __isl_keep isl_schedule *schedule) {
  static const char *macros[] = {"min", "max", "floord"};
  struct name_set live = {NULL, 0, 0};
  isl_union_set *domain;
  isl_size n_param;

  for (size_t i = 0; i < sizeof(macros) / sizeof(macros[0]); i++)
    name_set_add(reserved, macros[i]);

  n_param = isl_set_dim(scop->context, isl_dim_param);
  for (isl_size i = 0; i < n_param; i++)
    name_set_add(reserved,
                 isl_set_get_dim_name(scop->context, isl_dim_param, i));

  domain = isl_schedule_get_domain(schedule);
  isl_union_set_foreach_set(domain, &_add_tuple_name, &live);
  isl_union_set_free(domain);

  for (int i = 0; i < scop->n_stmt; i++) {
    struct pet_stmt *stmt = scop->stmts[i];
    isl_space *space = pet_stmt_get_space(stmt);
    const char *name = isl_space_get_tuple_name(space, isl_dim_set);
    int is_live = name && name_set_has(&live, name);

    isl_space_free(space);
    if (!is_live)
      continue;
    pet_tree_foreach_access_expr(stmt->body, &_add_accessed_name, reserved);
    pet_tree_foreach_expr(stmt->body, &_add_called_names, reserved);
  }
  name_set_free(&live);
}

/* The name a single schedule dimension is derived from, together with the
 * position in "scop" of the statement it was taken from.  A schedule
 * dimension may be described by one expression per statement, while isl
 * supports a single iterator name per depth, so "rank" is used to always
 * pick the statement that comes first in the original source.
 */
struct candidate {
  char *name;
  int rank;
  struct pet_scop *scop;
};

/* The position in "scop" of the statement "pa" schedules, or scop->n_stmt if
 * it cannot be determined.
 *
 * isl_union_pw_aff_foreach_pw_aff() visits the expressions in the order of
 * isl's internal hash table, which has nothing to do with the order of the
 * statements in the source, hence this lookup.
 */
static int
_stmt_rank(__isl_keep struct pet_scop *scop, __isl_keep isl_pw_aff *pa) {
  isl_space *space = isl_pw_aff_get_domain_space(pa);
  const char *name = isl_space_get_tuple_name(space, isl_dim_set);
  int rank = scop->n_stmt;

  for (int i = 0; name && i < scop->n_stmt; i++) {
    isl_space *stmt_space = pet_stmt_get_space(scop->stmts[i]);
    const char *stmt_name = isl_space_get_tuple_name(stmt_space, isl_dim_set);
    int match = stmt_name && !strcmp(name, stmt_name);

    isl_space_free(stmt_space);
    if (match) {
      rank = i;
      break;
    }
  }
  isl_space_free(space);
  return rank;
}

/* isl_union_pw_aff_foreach_pw_aff callback determining the original iterator
 * name the schedule dimension described by "pa" was derived from.
 *
 * If "pa" depends on exactly one iteration domain dimension, then the name
 * of that dimension is the candidate.  This includes the dimensions
 * introduced by tiling, scaling and shifting (`i - (i) mod 32`, `3i`,
 * `-2i`, ...), which all still refer to a single original iterator;
 * isl_pw_aff_involves_dims() sees through the div definitions of the tiled
 * forms.  Dimensions mixing several iterators (skewing) get no candidate.
 *
 * "user" points to the candidate of a single schedule dimension.  The
 * statement that comes first in the source wins.
 */
static isl_stat
_candidate_from_pw_aff(__isl_take isl_pw_aff *pa, void *user) {
  struct candidate *candidate = user;
  int rank = _stmt_rank(candidate->scop, pa);
  int found = -1;
  isl_size n;

  if (candidate->name && rank >= candidate->rank) {
    isl_pw_aff_free(pa);
    return isl_stat_ok;
  }
  n = isl_pw_aff_dim(pa, isl_dim_in);
  for (isl_size i = 0; i < n; i++) {
    if (isl_pw_aff_involves_dims(pa, isl_dim_in, i, 1) != isl_bool_true)
      continue;
    if (found >= 0) {
      found = -1;
      break;
    }
    found = i;
  }
  if (found >= 0) {
    const char *name = isl_pw_aff_get_dim_name(pa, isl_dim_in, found);
    char *copy = name ? strdup(name) : NULL;

    if (copy) {
      free(candidate->name);
      candidate->name = copy;
      candidate->rank = rank;
    }
  }
  isl_pw_aff_free(pa);
  return isl_stat_ok;
}

/* The candidates of all schedule dimensions, indexed by depth.
 */
struct candidates {
  struct candidate *c;
  size_t n;
};

/* isl_schedule_foreach_schedule_node_top_down callback collecting the
 * candidate names of the schedule dimensions of "node".
 *
 * Only band nodes introduce schedule dimensions.  Member "k" of a band at
 * schedule depth "depth" describes the loop at depth "depth + k".
 */
static isl_bool
_collect_candidates(__isl_keep isl_schedule_node *node, void *user) {
  struct candidates *candidates = user;
  isl_multi_union_pw_aff *mupa;
  isl_size depth, n_member;

  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return isl_bool_true;
  depth = isl_schedule_node_get_schedule_depth(node);
  n_member = isl_schedule_node_band_n_member(node);
  if (depth < 0 || n_member < 0)
    return isl_bool_error;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  for (isl_size k = 0; k < n_member; k++) {
    size_t d = (size_t)depth + (size_t)k;
    isl_union_pw_aff *upa;

    if (d >= candidates->n ||
        (candidates->c[d].name && candidates->c[d].rank == 0))
      continue;
    upa = isl_multi_union_pw_aff_get_at(mupa, k);
    isl_union_pw_aff_foreach_pw_aff(upa, &_candidate_from_pw_aff,
                                    &candidates->c[d]);
    isl_union_pw_aff_free(upa);
  }
  isl_multi_union_pw_aff_free(mupa);
  return isl_bool_true;
}

/* Is "name" usable as the name of a loop iterator in the generated code?
 *
 * The names come from a C parser, so this only rejects the degenerate cases
 * of a schedule that was not derived from C source.
 */
static int
_is_identifier(const char *name) {
  if (!name || (!isalpha((unsigned char)name[0]) && name[0] != '_'))
    return 0;
  for (const char *c = name + 1; *c; c++)
    if (!isalnum((unsigned char)*c) && *c != '_')
      return 0;
  return 1;
}

/* Write a name based on "base" that does not appear in "taken" to "buffer",
 * by appending `_1`, `_2`, ... to "base" until the name is free.
 *
 * "base" is at most ITERATOR_BASE_SIZE long and "buffer" is
 * ITERATOR_NAME_SIZE long, so the suffix never gets truncated (which would
 * make this loop spin forever).
 */
static void
_unique_name(char *buffer, size_t size, const char *base,
             const struct name_set *taken) {
  snprintf(buffer, size, "%s", base);
  for (unsigned i = 1; name_set_has(taken, buffer); i++)
    snprintf(buffer, size, "%s_%u", base, i);
}

/* Write the name of the loop iterator for schedule dimension "depth" to
 * "buffer".
 *
 * Use "candidate", the original iterator this dimension was derived from,
 * if there is one, and fall back to the depth based name otherwise.  Either
 * way the name is made unique with respect to "taken", which holds both the
 * identifiers the generated code must not shadow and the names of the outer
 * loops: isl uses a single list of iterator names for all branches of the
 * schedule tree, so a name reused at a deeper level would shadow itself.
 * Tiling for instance turns an `i` loop into an `i` and an `i_1` loop.
 */
static void
_iterator_name(char *buffer, size_t size, const char *candidate, size_t depth,
               const struct name_set *taken) {
  char base[ITERATOR_BASE_SIZE];

  if (_is_identifier(candidate))
    snprintf(base, sizeof(base), "%s", candidate);
  else
    snprintf(base, sizeof(base), "_tadashi_%zu", depth);
  _unique_name(buffer, size, base, taken);
}

/* Construct the names of the "num_iterators" loop iterators of the code
 * generated for "schedule", preserving the iterator names of the original
 * source where possible.
 */
static __isl_give isl_id_list *
_iterator_list(isl_ctx *ctx, __isl_keep struct pet_scop *scop,
               __isl_keep isl_schedule *schedule, size_t num_iterators) {
  struct candidate *c = calloc(num_iterators, sizeof(*c));
  struct candidates candidates = {c, num_iterators};
  struct name_set taken = {NULL, 0, 0};
  isl_id_list *iterators;

  collect_reserved_names(&taken, scop, schedule);
  if (c) {
    for (size_t d = 0; d < num_iterators; d++) {
      c[d].rank = scop->n_stmt;
      c[d].scop = scop;
    }
    isl_schedule_foreach_schedule_node_top_down(schedule, &_collect_candidates,
                                                &candidates);
  }

  iterators = isl_id_list_alloc(ctx, num_iterators);
  for (size_t d = 0; d < num_iterators; d++) {
    char buffer[ITERATOR_NAME_SIZE];

    _iterator_name(buffer, sizeof(buffer), c ? c[d].name : NULL, d, &taken);
    name_set_add(&taken, buffer);
    iterators = isl_id_list_add(iterators, isl_id_alloc(ctx, buffer, NULL));
  }

  for (size_t d = 0; c && d < num_iterators; d++)
    free(c[d].name);
  free(c);
  name_set_free(&taken);
  return iterators;
}

__isl_give isl_printer *
codegen(__isl_take isl_printer *p, __isl_keep struct pet_scop *scop,
        __isl_take isl_schedule *schedule) {

  int indent;
  isl_ast_build *build;
  isl_ast_node *node;
  isl_ast_print_options *print_options;
  isl_id_to_id *id2stmt;
  isl_ctx *ctx = isl_printer_get_ctx(p);
  id2stmt = set_up_id2stmt(scop);
  build = isl_ast_build_alloc(ctx);
  build = isl_ast_build_set_at_each_domain(build, at_domain, id2stmt);
  build = isl_ast_build_set_after_each_mark(build, after_mark, NULL);
  size_t num_iterators = _schedule_num_iterators(schedule);
  isl_id_list *iterators = _iterator_list(ctx, scop, schedule, num_iterators);
  build = isl_ast_build_set_iterators(build, iterators);
  node = isl_ast_build_node_from_schedule(build, schedule);
  print_options = isl_ast_print_options_alloc(ctx);
  print_options =
      isl_ast_print_options_set_print_user(print_options, print_user, id2stmt);
  print_options =
      isl_ast_print_options_set_print_for(print_options, print_for, NULL);

  // this puts stuff to the beginning of the line
  p = isl_printer_set_indent_prefix(p, "");

  p = print_str_on_line(p, "#pragma scop");
  p = isl_printer_indent(p, 2);
  p = print_declarations(p, build, scop, &indent);
  p = print_macros(p, node);
  p = isl_ast_node_print(node, p, print_options);
  p = print_end_declarations(p, indent);
  p = isl_printer_indent(p, -2);
  p = print_str_on_line(p, "#pragma endscop");
  isl_ast_node_free(node);
  isl_ast_build_free(build);
  isl_id_to_id_free(id2stmt);
  return p;
}
