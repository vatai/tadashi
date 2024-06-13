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

#include "transformations.h"

__isl_give isl_union_set_list *
_fuse_get_filters(isl_schedule_node **node, __isl_take isl_union_set *filter,
                  int idx1, int idx2) {
  isl_union_set_list *filters;
  isl_ctx *ctx = isl_schedule_node_get_ctx(*node);
  isl_size size = isl_schedule_node_n_children(*node) - 1;
  filters = isl_union_set_list_alloc(ctx, size);
  for (int i = 0; i < size; i++) {
    isl_union_set *f;
    if (i >= idx2) {
      *node = isl_schedule_node_child(*node, i + 1);
      f = isl_schedule_node_filter_get_filter(*node);
      *node = isl_schedule_node_parent(*node);
    } else if (i == idx1) {
      f = filter;
    } else { // i < idx2
      *node = isl_schedule_node_child(*node, i);
      f = isl_schedule_node_filter_get_filter(*node);
      *node = isl_schedule_node_parent(*node);
    }
    filters = isl_union_set_list_insert(filters, i, f);
  }
  return filters;
}

__isl_give isl_schedule_node *
_fuse_insert_outer_shorter_sequence(__isl_take isl_schedule_node *node,
                                    int idx1, int idx2) {
  // Insert new sequence node with **one less filter nodes** above the
  // original sequence node. The inner, original sequence has the
  // original number of filters, with all but 2 being empty. Location
  // is at the new node.

  isl_union_set_list *filters;
  isl_union_set *filter;
  node = isl_schedule_node_child(node, idx1);
  filter = isl_schedule_node_filter_get_filter(node);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_child(node, idx2);
  filter =
      isl_union_set_union(filter, isl_schedule_node_filter_get_filter(node));
  node = isl_schedule_node_parent(node);
  filters = _fuse_get_filters(&node, filter, idx1, idx2);
  node = isl_schedule_node_insert_sequence(node, filters);
  return node;
}

struct _fuse_result_t {
  isl_union_set *filter;
  isl_union_set_list *filters;
  isl_multi_union_pw_aff *mupa;
};

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

  int idx1 = 1, idx2 = 3;
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
  // printf("BEFORE:\n%s\n\n", isl_schedule_node_to_str(node));
  node = tadashi_fuse(node, idx1, idx2);
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
