#include <stdio.h>

#include <isl/id.h>
#include <isl/set_type.h>
#include <isl/space.h>

int main(int argc, char *argv[]) {
  printf("Hello world!\n");
  isl_ctx *ctx = isl_ctx_alloc();

  isl_id *id1 = isl_id_alloc(ctx, "id1", NULL);
  isl_space *spaces[] = {isl_space_alloc(ctx, 3, 2, 1),
                         isl_space_params_alloc(ctx, 3),
                         isl_space_set_alloc(ctx, 3, 2), isl_space_unit(ctx)};

  const int num_spaces = sizeof(spaces) / sizeof(*spaces);
  for (int i = 0; i < num_spaces; ++i)
    printf("%d %d %d\n", isl_space_is_params(spaces[i]),
           isl_space_is_set(spaces[i]), isl_space_is_map(spaces[i]));

  for (int i = 0; i < num_spaces; ++i)
    isl_space_free(spaces[i]);
  isl_id_free(id1);
  isl_ctx_free(ctx);
  return 0;
}
