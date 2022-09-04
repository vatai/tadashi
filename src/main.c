#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include <isl/options.h>
#include <isl/schedule_node.h>
#include <isl/space.h>
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

struct user_t {
  isl_schedule_node *node;
  isl_multi_union_pw_aff *mupa;
};

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

void codegen(isl_ctx *ctx, isl_schedule *schedule) {
  isl_ast_build *build;
  isl_ast_node *ast;
  build = isl_ast_build_alloc(ctx);
  assert(build != NULL);
  ast = isl_ast_build_node_from_schedule(build, isl_schedule_copy(schedule));
  printf("code:\n%s\n", isl_ast_node_to_C_str(ast));
  isl_ast_node_free(ast);
  isl_ast_build_free(build);
}

isl_bool proc_node(__isl_keep isl_schedule_node *node, void *user) {
  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return isl_bool_true;

  printf(">>> %s\n", isl_schedule_node_to_str(node));

  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(node);
  isl_ctx *ctx = isl_multi_union_pw_aff_get_ctx(mupa);
  isl_multi_aff *ma = isl_multi_aff_read_from_str( //
      ctx, "[n] -> { L_0[i0] -> [(n - i0)] }");

  mupa = isl_multi_union_pw_aff_apply_multi_aff(mupa, isl_multi_aff_copy(ma));
  printf(">>mupa+: %s\n", isl_multi_union_pw_aff_to_str(mupa));

  struct user_t *data = (struct user_t *)user;

  node = isl_schedule_node_delete(node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_copy(mupa));

  data->mupa = isl_multi_union_pw_aff_copy(mupa);
  data->node = isl_schedule_node_copy(node);

  isl_multi_aff_free(ma);
  isl_multi_union_pw_aff_free(mupa);
  return isl_bool_false;
}

isl_schedule *mod_schedule(struct user_t *data) {
  isl_schedule_node *node = isl_schedule_node_delete(data->node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_copy(data->mupa));
  return isl_schedule_node_get_schedule(node);
}

int main(int argc, char *argv[]) {
  struct options *options = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);
  pet_scop *scop = pet_scop_extract_from_C_source(ctx, filename, "g");

  struct user_t *user = (struct user_t *)malloc(sizeof(struct user_t));
  // print_scop(scop);
  isl_schedule_foreach_schedule_node_top_down(scop->schedule, proc_node, user);

  isl_schedule *schedule = mod_schedule(user);
  codegen(ctx, schedule);

  isl_multi_union_pw_aff_free(user->mupa);
  isl_schedule_node_free(user->node);
  isl_schedule_free(schedule);
  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("DONE!\n");
  return 0;
}
