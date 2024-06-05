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
      isl_union_set_read_from_str(ctx, "[N] -> {S_0[i,j] : i mod 5 = 0 }"));
  node = isl_schedule_node_order_before(
      node,
      isl_union_set_read_from_str(ctx, "[N] -> {S_0[i,j] : i mod 5 = 1 }"));
  node = isl_schedule_node_order_before(
      node,
      isl_union_set_read_from_str(ctx, "[N] -> {S_0[i,j] : i mod 5 = 2 }"));
  node = isl_schedule_node_order_before(
      node,
      isl_union_set_read_from_str(ctx, "[N] -> {S_0[i,j] : i mod 5 = 3 }"));
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);
  printf("BEFORE:\n%s\n\n", isl_schedule_node_to_str(node));

  // TODO: idx1 = min(pos1, pos2);
  // TODO: idx2 = max(pos1, pos2)
  int idx1 = 1, idx2 = 3;
  isl_union_set_list *filters;
  isl_union_set *filter;
  isl_multi_union_pw_aff *mupa;
  isl_size size = isl_schedule_node_n_children(node) - 1;
  printf("size = %d\n", size);
  filters = isl_union_set_list_alloc(ctx, size);
  node = isl_schedule_node_child(node, idx1);
  filter = isl_schedule_node_filter_get_filter(node);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_child(node, idx2);
  filter =
      isl_union_set_union(filter, isl_schedule_node_filter_get_filter(node));
  node = isl_schedule_node_parent(node);
  for (int i = 0; i < size; i++) {
    isl_union_set *f;
    if (i >= idx2) {
      node = isl_schedule_node_child(node, i + 1);
      f = isl_schedule_node_filter_get_filter(node);
      node = isl_schedule_node_parent(node);
    } else if (i == idx1) {
      f = filter;
    } else { // i < idx2
      node = isl_schedule_node_child(node, i);
      f = isl_schedule_node_filter_get_filter(node);
      node = isl_schedule_node_parent(node);
    }
    filters = isl_union_set_list_insert(filters, i, f);
  }
  node = isl_schedule_node_insert_sequence(node, filters);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);

  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_next_sibling(node);
  node = isl_schedule_node_first_child(node);

  node = isl_schedule_node_child(node, idx1);
  filter = isl_schedule_node_filter_get_filter(node);
  filters = isl_union_set_list_from_union_set(isl_union_set_copy(filter));
  node = isl_schedule_node_first_child(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  mupa = isl_multi_union_pw_aff_intersect_domain(mupa, filter);
  node = isl_schedule_node_delete(node);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);

  node = isl_schedule_node_child(node, idx2);
  filter = isl_schedule_node_filter_get_filter(node);
  filters = isl_union_set_list_insert(filters, 1, isl_union_set_copy(filter));
  node = isl_schedule_node_first_child(node);
  mupa = isl_multi_union_pw_aff_union_add(
      mupa, isl_multi_union_pw_aff_intersect_domain(
                isl_schedule_node_band_get_partial_schedule(node), filter));
  node = isl_schedule_node_delete(node);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);

  node = isl_schedule_node_insert_sequence(node, filters);
  node = isl_schedule_node_insert_partial_schedule(node, mupa);

  printf("AFTER:\n%s\n\n", isl_schedule_node_to_str(node));
  // TODO ///////////////////////////////////
  // GROUP
  // node = isl_schedule_node_group(node, isl_id_read_from_str(ctx, "S_0"));
  // printf("GROUP:\n%s\n\n", isl_schedule_node_to_str(node));

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
