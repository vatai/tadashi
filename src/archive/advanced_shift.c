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
  file = fopen("build/_deps/polybench-src/linear-algebra/blas/gemm/"
               "gemm.c.0.tadashi.yaml",
               "r");
  assert(file != 0);
  isl_schedule *schedule = isl_schedule_read_from_file(ctx, file);
  fclose(file);
  isl_schedule_node *node = isl_schedule_get_root(schedule);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_child(node, 1);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_child(node, 1);
  node = isl_schedule_node_first_child(node);
  // isl_schedule_node_dump(node);

  node = isl_schedule_node_band_scale(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, 60))));
  // printf("BAND_SCALE:\n%s\n\n", isl_schedule_node_to_str(node));

  node = isl_schedule_node_band_scale_down(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, 3))));
  // printf("BAND_SCALE_DOWN:\n%s\n\n", isl_schedule_node_to_str(node));

  isl_space *space = isl_schedule_node_band_get_space(node);
  isl_space_dump(space);
  isl_union_set *domain = isl_schedule_node_get_domain(node);
  isl_union_set_dump(domain);
  // space: [this] -> L_andthis[maybe_this]
  node = isl_schedule_node_band_shift(
      node, isl_multi_union_pw_aff_read_from_str(
                ctx, "[ni, nj] -> L_1[{ S_3[i,j] -> [(300)]; S_2[i,j]->[(400)] } ]"));
  printf("SHIFT:\n%s\n\n", isl_schedule_node_to_str(node));

  isl_schedule_node_free(node);
  isl_schedule_free(schedule);
  isl_space_free(space);
  isl_union_set_free(domain);
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
