#include <stdio.h>

#include <isl/ctx.h>
#include <isl/set.h>
#include <isl/space.h>

void param_space(isl_ctx *ctx) {
  unsigned int nparam = 3, n_in = 0, n_out = 0;
  isl_space *space = isl_space_alloc(ctx, nparam, n_in, n_out);
  isl_space *pspace = isl_space_params_alloc(ctx, nparam);
  isl_space *sspace = isl_space_set_alloc(ctx, nparam, n_out);
  isl_basic_set *set = isl_basic_set_empty(pspace);

  isl_space *uspace = isl_space_unit(ctx);
  uspace = isl_space_add_dims(uspace, isl_dim_param, 3);
  uspace = isl_space_set_dim_name(uspace, isl_dim_param, 2, "buz");

  printf("set %s\n", isl_basic_set_to_str(set));

  puts("");

  printf("space: %s\n", isl_space_to_str(space));
  printf("pspace: %s\n", isl_space_to_str(pspace));
  printf("sspace: %s\n", isl_space_to_str(sspace));
  printf("uspace: %s\n", isl_space_to_str(uspace));

  puts("");

  printf("is param space %d\n", isl_space_is_params(space));
  printf("is param pspace %d\n", isl_space_is_params(pspace));
  printf("is param pspace %d\n", isl_space_is_params(sspace));
  printf("is param uspace %d\n", isl_space_is_params(uspace));

  isl_basic_set_free(set);
  isl_space_free(space);
  isl_space_free(pspace);
  isl_space_free(sspace);
  isl_space_free(uspace);
}

void sets(isl_ctx *ctx) {
  isl_space *space = isl_space_unit(ctx);
  isl_space_add_dims(space, isl_dim_param, 1);
  isl_space_add_dims(space, isl_dim_out, 2);
  // isl_space_add_dims(space, isl_dim_in, 2); // all return `(null)`
  printf("space: %s\n", isl_space_to_str(space));

  isl_basic_set *bset = isl_basic_set_universe(isl_space_copy(space));
  printf("bset_universe: %s\n", isl_basic_set_to_str(bset));
  fflush(stdout);
  isl_basic_set_free(bset);

  isl_basic_set *bempty = isl_basic_set_empty(isl_space_copy(space));
  printf("bset_empty: %s\n", isl_basic_set_to_str(bempty));
  fflush(stdout);
  isl_basic_set_free(bempty);

  isl_set *set = isl_set_universe(isl_space_copy(space));
  printf("set_universe: %s\n", isl_set_to_str(set));
  fflush(stdout);
  isl_set_free(set);

  isl_set *empty = isl_set_empty(isl_space_copy(space));
  printf("set_empty: %s\n", isl_set_to_str(empty));
  fflush(stdout);
  isl_set_free(empty);

  isl_space_free(space);
}

int main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  // param_space(ctx);
  sets(ctx);

  isl_ctx_free(ctx);
}
