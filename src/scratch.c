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
  file = fopen("./examples/fused-no.c.0.tadashi.isl", "r");
  assert(file != 0);
  isl_union_map *umap = isl_union_map_read_from_file(ctx, file);
  // isl_union_map_dump(umap);
  fclose(file);
  file = fopen("./examples/fused-no.c.0.tadashi.yaml", "r");
  assert(file != 0);
  isl_schedule *schedule = isl_schedule_read_from_file(ctx, file);
  // isl_schedule_dump(schedule);
  fclose(file);

  isl_schedule_node *node = isl_schedule_get_root(schedule);
  isl_schedule_node_dump(node);
  node = isl_schedule_node_first_child(node);
  assert(isl_schedule_node_get_type(node) == isl_schedule_node_sequence);

  // traverse branch 0
  node = isl_schedule_node_child(node, 0);
  isl_union_set *f0 = isl_schedule_node_filter_get_filter(node);
  node = isl_schedule_node_first_child(node);
  isl_multi_union_pw_aff *p0 =
      isl_schedule_node_band_get_partial_schedule(node);

  // go back
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);

  // traverse branch 1
  node = isl_schedule_node_child(node, 1);
  isl_union_set *f1 = isl_schedule_node_filter_get_filter(node);
  node = isl_schedule_node_first_child(node);
  isl_union_set *f =
      isl_union_set_union(isl_union_set_copy(f0), isl_union_set_copy(f1));
  isl_multi_union_pw_aff *p1 =
      isl_schedule_node_band_get_partial_schedule(node);

  isl_schedule_node *subtree = isl_schedule_node_get_child(node, 0);
  // isl_schedule_node_dump(subtree);
  // node = isl_schedule_node_delete(node);

  // node = isl_schedule_node_parent(node);
  node = isl_schedule_node_cut(node);
  node = isl_schedule_node_parent(node);

  isl_schedule_node_dump(node);

  // node = isl_schedule_node_insert_filter(node, f);
  isl_union_set_list *flist = isl_union_set_list_from_union_set(f0);
  flist = isl_union_set_list_insert(flist, 1, f1);

  isl_schedule_node_free(subtree);
  isl_schedule_node_dump(node);
  isl_multi_union_pw_aff_dump(p1);
  isl_union_set_free(f);
  isl_union_set_list_free(flist);

  isl_multi_union_pw_aff_free(p0);
  isl_multi_union_pw_aff_free(p1);
  isl_schedule_node_free(node);
  isl_schedule_free(schedule);
  isl_union_map_free(umap);

  isl_ctx_free(ctx);
  printf("Bye!\n");
}
