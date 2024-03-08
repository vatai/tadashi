/*
 * When I wrote this only God and I knew what I was doing. Now only
 * god knows.  -- common comment in source code
 *
 * Emil Vatai
 *
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include <isl/options.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_set.h>

#include <pet.h>

const char filename[] = "../examples/hello.c";

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
  isl_schedule *schedule;
};

void code_gen(isl_ctx *ctx, isl_schedule *schedule) {
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
  struct user_t *data = (struct user_t *)user;

  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(node);
  isl_ctx *ctx = isl_multi_union_pw_aff_get_ctx(mupa);
  isl_multi_aff *ma = isl_multi_aff_read_from_str( //
      ctx, "[n] -> { L_0[i0] -> [( -i0 )] }");

  mupa = isl_multi_union_pw_aff_apply_multi_aff(mupa, isl_multi_aff_copy(ma));
  node = isl_schedule_node_delete(node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_copy(mupa));
  node = isl_schedule_node_delete(node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_copy(mupa));

  data->schedule = isl_schedule_node_get_schedule(node);

  isl_multi_aff_free(ma);
  isl_multi_union_pw_aff_free(mupa);
  return isl_bool_true;
}

int main(int argc, char *argv[]) {
  struct options *options = options_new_with_defaults();
  isl_ctx *ctx = isl_ctx_alloc_with_options(&options_args, options);
  pet_scop *scop = pet_scop_extract_from_C_source(ctx, filename, "g");
  code_gen(ctx, scop->schedule);

  struct user_t *user = (struct user_t *)malloc(sizeof(struct user_t));
  isl_schedule_foreach_schedule_node_top_down(scop->schedule, proc_node, user);
  code_gen(ctx, user->schedule);
  isl_schedule_free(user->schedule);
  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("DONE!\n");
  return 0;
}
