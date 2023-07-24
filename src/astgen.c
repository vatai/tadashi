#include <isl/ast_type.h>
#include <isl/id.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/space_type.h>
#include <stdio.h>

#include <isl/ast.h>
#include <isl/ast_build.h>
#include <isl/ctx.h>
#include <isl/options.h>
#include <isl/space.h>
#include <isl/union_set.h>
#include <pet.h>

void astgen(isl_ctx *ctx, pet_scop *scop);
isl_set *get_domain(isl_ctx *ctx);

int main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();

  char file[] = "../examples/depnodep.c";
  pet_scop *scop = pet_scop_extract_from_C_source(ctx, file, 0);

  astgen(ctx, scop);

  pet_scop_free(scop);
  isl_ctx_free(ctx);
  printf("Done!\n");
  return 0;
}

void astgen(isl_ctx *ctx, pet_scop *scop) {
  isl_schedule *schedule;
  isl_schedule_node *root;
  isl_ast_build *build = 0;
  isl_ast_node *ast = 0;
  isl_ast_expr *expr = 0;
  isl_set *domain = 0;

  schedule = pet_scop_get_schedule(scop);
  root = isl_schedule_get_root(schedule);
  // printf("root: %s\n", isl_schedule_node_to_str(root));

  // domain = get_domain(ctx);

  build = isl_ast_build_alloc(ctx);
  // build = isl_ast_build_from_context(isl_set_copy(domain));

  ast = isl_ast_build_node_from_schedule(build, isl_schedule_copy(schedule));
  printf("ast: %s\n", isl_ast_node_to_str(ast));
  printf("ast: %s\n", isl_ast_node_to_C_str(ast));
  printf("type(ast) == for: %d\n",
         isl_ast_node_get_type(ast) == isl_ast_node_for);

  expr = isl_ast_node_for_get_cond(ast);
  printf("expr (cond): %s\n", isl_ast_expr_to_str(expr));
  printf("expr (cond): %s\n", isl_ast_expr_to_C_str(expr));

  if (expr)
    isl_ast_expr_free(expr);
  if (ast)
    isl_ast_node_free(ast);
  if (domain)
    isl_set_free(domain);
  if (build)
    isl_ast_build_free(build);
  isl_schedule_node_free(root);
  isl_schedule_free(schedule);
}

isl_set *get_domain(isl_ctx *ctx) {
  isl_space *space;
  isl_set *domain;
  space = isl_space_alloc(ctx, 1, 0, 0);
  space = isl_space_set_dim_name(space, isl_dim_param, 0, "N");
  printf("space: %s\n", isl_space_to_str(space));

  // domain = isl_set_from_union_set(isl_schedule_get_domain(schedule));
  // domain = isl_set_read_from_str(ctx, "{ N : 1 <= N <= 100 }");
  domain = isl_set_nat_universe(isl_space_copy(space));
  printf("domain: %s\n", isl_set_to_str(domain));

  isl_space_free(space);
  return domain;
}
