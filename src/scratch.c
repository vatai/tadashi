#include <assert.h>
#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/id.h>
#include <isl/map_type.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/space_type.h>
#include <isl/union_map_type.h>
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
  // isl_union_map_dump(umap);
  fclose(file);
  file = fopen("./examples/depnodep.c.0.tadashi.yaml", "r");
  assert(file != 0);
  isl_schedule *schedule = isl_schedule_read_from_file(ctx, file);
  // isl_schedule_dump(schedule);
  fclose(file);
  isl_schedule_node *node = isl_schedule_get_root(schedule);
  node = isl_schedule_node_first_child(node);

  // ORDER_BEFORE
  node = isl_schedule_node_order_before(
      node,
      isl_union_set_read_from_str(ctx, "[N] -> {S_0[i,j] : i mod 2 = 0 }"));
  printf("ORDER_BEFORE:\n%s\n\n", isl_schedule_node_to_str(node));

  // BAND_SCALE
  // node = isl_schedule_node_band_scale(
  //     node, isl_multi_val_from_val_list(
  //               isl_schedule_node_band_get_space(node),
  //               isl_val_list_from_val(isl_val_int_from_si(ctx, 6))));
  // printf("BAND_SCALE:\n%s\n\n", isl_schedule_node_to_str(node));

  // BAND_SCALE_DOWN
  // node = isl_schedule_node_band_scale_down(
  //     node, isl_multi_val_from_val_list(
  //               isl_schedule_node_band_get_space(node),
  //               isl_val_list_from_val(isl_val_int_from_si(ctx, 3))));
  // printf("BAND_SCALE_DOWN:\n%s\n\n", isl_schedule_node_to_str(node));

  // GROUP
  // node = isl_schedule_node_group(node, isl_id_read_from_str(ctx, "S_0"));
  // printf("GROUP:\n%s\n\n", isl_schedule_node_to_str(node));

  isl_multi_union_pw_aff *tmp =
      isl_multi_union_pw_aff_read_from_str(ctx, "[N] -> [{ [i] -> [2i] }]");
  isl_multi_union_pw_aff_dump(
      isl_schedule_node_band_get_partial_schedule(node));
  node = isl_schedule_node_band_shift(node, tmp);

  // TODO ///////////////////////////////////
  // node = isl_schedule_node_parent(node);
  // printf("SPLICE_CHILDREN:\n%s\n\n", isl_schedule_node_to_str(node));
  // node = isl_schedule_node_sequence_splice_children(node);

  isl_schedule_node_free(node);
  isl_schedule_free(schedule);
  isl_union_map_free(umap);
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
