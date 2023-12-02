#include <assert.h>
#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/space.h>
#include <isl/space_type.h>
#include <isl/val.h>
#include <stdio.h>

#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/union_map.h>
#include <isl/union_set.h>

int main() {
  printf("Hello\n");
  isl_ctx *ctx = isl_ctx_alloc();

  FILE *file;
  file = fopen("./examples/depnodep.c.0.tadashi.isl", "r");
  assert(file != 0);
  isl_union_map *umap = isl_union_map_read_from_file(ctx, file);
  isl_union_map_dump(umap);
  fclose(file);
  file = fopen("./examples/depnodep.c.0.tadashi.yaml", "r");
  assert(file != 0);
  isl_schedule *schedule = isl_schedule_read_from_file(ctx, file);
  // isl_schedule_dump(schedule);
  fclose(file);

  isl_schedule_node *n = isl_schedule_get_root(schedule);
  n = isl_schedule_node_first_child(n);
  isl_schedule_node_dump(n);

  n = isl_schedule_node_band_tile(
      n, isl_multi_val_from_val_list(
             isl_schedule_node_band_get_space(n),
             isl_val_list_from_val(isl_val_int_from_si(ctx, 4))));

  n = isl_schedule_node_first_child(n);
  isl_schedule_node_dump(n);
  isl_multi_union_pw_aff *mupa = isl_schedule_node_band_get_partial_schedule(n);
  n = isl_schedule_node_delete(n);
  isl_schedule_node_dump(n);
  n = isl_schedule_node_first_child(n);
  n = isl_schedule_node_insert_partial_schedule(n, mupa);

  mupa = isl_multi_union_pw_aff_read_from_str(
      ctx, "[N] -> L_1[{ S_0[i, j] -> [(j)] }, { S_0[i, j] -> [(i+j)] }]");
  isl_space *space = isl_multi_union_pw_aff_get_space(mupa);
  isl_size size = isl_space_dim(space, isl_dim_out);
  // todo try isl_val instead of name
  printf("dim0: %s\n", isl_space_get_dim_name(space, isl_dim_out, 0));
  printf("dim1: %s\n", isl_space_get_dim_name(space, isl_dim_out, 1));
  printf("dims: %d\n", isl_space_dim(space, isl_dim_out));
  isl_space_free(space);
  isl_multi_union_pw_aff_free(mupa);
  printf("size: %d\n", size);

  isl_schedule_node_dump(n);

  isl_schedule_node_free(n);
  isl_schedule_free(schedule);
  isl_union_map_free(umap);

  isl_ctx_free(ctx);
  printf("Bye!\n");
}
