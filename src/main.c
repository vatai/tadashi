#include <assert.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/arg.h>
#include <isl/id_to_pw_aff.h>
#include <isl/options.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <pet.h>

const char filename[] = "../src/hello.c";

struct options {
  struct isl_options *isl;
  struct pet_options *pet;
  char *schedule;
  char *code;
  unsigned tree;
};

ISL_ARGS_START(struct options, options_args)
ISL_ARG_CHILD(struct options, isl, "isl", &isl_options_args, "isl options")
ISL_ARG_CHILD(struct options, pet, NULL, &pet_options_args, "pet options")
ISL_ARG_ARG(struct options, schedule, "schedule", NULL)
ISL_ARG_ARG(struct options, code, "code", NULL)
ISL_ARG_BOOL(struct options, tree, 0, "tree", 0,
             "input schedule is specified as schedule tree")
ISL_ARGS_END

ISL_ARG_DEF(options, struct options, options_args)

void print_scop(pet_scop *scop) {
  printf("n_arrays: %d\n", scop->n_array);
  for (int i = 0; i < scop->n_array; ++i) {
    printf("arrays[%d]->context: %s\n", i,
           isl_set_to_str(scop->arrays[i]->context));
    printf("arrays[%d]->extent: %s\n", i,
           isl_set_to_str(scop->arrays[i]->extent));
  }

  printf("context: %s\n", isl_set_to_str(scop->context));

  printf("context_value: %s\n", isl_set_to_str(scop->context_value));

  printf("n_implication: %d\n", scop->n_implication);
  for (int i = 0; i < scop->n_implication; ++i) {
    printf("implications[%d]->extension: %s\n", i,
           isl_map_to_str(scop->implications[i]->extension));
    printf("implications[%d]->satisfied: %d\n", i,
           scop->implications[i]->satisfied);
  }

  printf("n_independence: %d\n", scop->n_independence);
  for (int i = 0; i < scop->n_independence; ++i) {
    printf("independences[%d]->filter: %s\n", i,
           isl_union_map_to_str(scop->independences[i]->filter));
    printf("independences[%d]->local: %s\n", i,
           isl_union_set_to_str(scop->independences[i]->local));
  }

  printf("n_stmt: %d\n", scop->n_stmt);
  for (int i = 0; i < scop->n_stmt; ++i) {
    struct pet_stmt *stmt = scop->stmts[i];
    /* printf("stmt[%d]->n_args: %d\n", i, stmt->n_arg); */
    /* for (int j = 0; j < stmt->n_arg; ++j) */
    /*   printf("stmt[%d]->args[%d]: %s\n", i, j, stmt->args[j]); */
    printf("stmt[%d]->domain: %s\n", i, isl_set_to_str(stmt->domain));
    printf("stmt[%d]->loc: %d\n", i, pet_loc_get_line(stmt->loc));
  }

  printf("n_type: %d\n", scop->n_type);
  for (int i = 0; i < scop->n_type; ++i) {
    printf("types[%d]->definition/name: %s/%s\n", i, //
           scop->types[i]->definition, scop->types[i]->name);
  }

  printf("schedule: %s\n", isl_schedule_to_str(scop->schedule));
}

void traverse_schedule(isl_schedule *schedule) {
  isl_union_set *domain;
  isl_schedule_node *node;
  enum isl_schedule_node_type type;
  const char msg[] = "domain: %s\n\n\n\n";

  domain = isl_schedule_get_domain(schedule);
  node = isl_schedule_get_root(schedule);
  printf(msg, isl_schedule_node_to_str(node));
  while (isl_schedule_node_has_children(node)) {
    node = isl_schedule_node_child(node, 0);
    printf(msg, isl_schedule_node_to_str(node));
  }

  isl_union_set_free(domain);
  isl_schedule_node_free(node);
}

int main(int argc, char *argv[]) {
  struct options *options;
  isl_ctx *ctx;
  pet_scop *scop;

  options = options_new_with_defaults();
  ctx = isl_ctx_alloc_with_options(&options_args, options);
  assert(ctx != NULL);

  scop = pet_scop_extract_from_C_source(ctx, filename, NULL);
  assert(scop != NULL);

  // print_scop(scop);

  traverse_schedule(scop->schedule);

  pet_scop_free(scop);
  isl_ctx_free(ctx);

  return 0;
}
