#include <isl/local_space.h>
#include <isl/space_type.h>
#include <stdio.h>

#include <isl/id.h>
#include <isl/set_type.h>
#include <isl/space.h>

int main(int argc, char *argv[]) {
  printf("Hello world!\n");
  isl_ctx *ctx = isl_ctx_alloc();

  isl_id *N_id = isl_id_alloc(ctx, "N", NULL);
  isl_id *M_id = isl_id_alloc(ctx, "M", NULL);
  isl_id *i_id = isl_id_alloc(ctx, "i", NULL);
  isl_id *j_id = isl_id_alloc(ctx, "j", NULL);
  const unsigned ndim = 2;

  // Spaces begin
  // params, set, map
  isl_space *spaces[] = {isl_space_alloc(ctx, 3, 2, 1),  // 0 0 1
                         isl_space_params_alloc(ctx, 3), // 1 1 0
                         isl_space_set_alloc(ctx, 3, 2), // 0 1 0
                         isl_space_unit(ctx)};           // 1 1 0
  const int num_spaces = sizeof(spaces) / sizeof(*spaces);
  for (int i = 0; i < num_spaces; ++i)
    printf("%d %d %d\n", //
           isl_space_is_params(spaces[i]),
           isl_space_is_set(spaces[i]), //
           isl_space_is_map(spaces[i]));
  // Spaces end

  isl_space *space = isl_space_unit(ctx);
  // isl_space *space = isl_space_set_alloc(ctx, 0, ndim);
  space = isl_space_add_param_id(space, N_id);
  space = isl_space_add_param_id(space, M_id);
  space = isl_space_add_dims(space, isl_dim_set, ndim);
  space = isl_space_set_dim_id(space, isl_dim_set, 0, i_id);
  space = isl_space_set_dim_id(space, isl_dim_set, 1, j_id);

  enum isl_dim_type type = isl_dim_all;
  printf("type: %d\n", type);
  printf("space dim: %d\n", isl_space_dim(space, type));

  // Print id names
  for (int pos = 0; pos < ndim; ++pos) {
    isl_id *tmp_id = isl_space_get_dim_id(space, isl_dim_set, pos);
    printf("id[%d]: %s\n", pos, isl_id_get_name(tmp_id));
    isl_id_free(tmp_id);
  }

  isl_space_free(space);
  // Spaces begin
  for (int i = 0; i < num_spaces; ++i)
    isl_space_free(spaces[i]);
  // Spaces end
  isl_id_free(N_id);
  isl_id_free(i_id);
  isl_ctx_free(ctx);
  return 0;
}
