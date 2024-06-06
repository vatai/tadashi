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

__isl_give isl_union_set_list *get_filters(isl_schedule_node **node,
                                           __isl_take isl_union_set *filter,
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
insert_outer_shorter_sequence(__isl_take isl_schedule_node *node, int idx1,
                              int idx2) {
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
  filters = get_filters(&node, filter, idx1, idx2);
  node = isl_schedule_node_insert_sequence(node, filters);
  return node;
}

struct result_t {
  isl_union_set *filter;
  isl_union_set_list *filters;
  isl_multi_union_pw_aff *mupa;
};

__isl_give isl_schedule_node *
get_filter_and_mupa(__isl_take isl_schedule_node *node, int idx,
                    struct result_t *result, isl_union_set_list **filters) {
  // Go down to first merged/non-empty filter and get the filter; Go
  // further down to the schedule node to get the schedule mupa and
  // restrict it to the filter. Go back up 2x (to the original node).
  isl_union_set *tmp;
  node = isl_schedule_node_child(node, idx);
  result->filter = isl_schedule_node_filter_get_filter(node);
  node = isl_schedule_node_first_child(node);
  result->mupa = isl_schedule_node_band_get_partial_schedule(node);
  result->mupa =
      isl_multi_union_pw_aff_intersect_domain(result->mupa, result->filter);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);
  tmp = isl_union_set_copy(result->filter);
  isl_size pos = isl_union_set_list_size(*filters);
  *filters = isl_union_set_list_insert(*filters, pos, tmp);
  return node;
}

__isl_give isl_schedule_node *tadashi_fuse(__isl_take isl_schedule_node *node,
                                           int idx1, int idx2) {
  isl_union_set_list *filters;
  isl_multi_union_pw_aff *mupa;
  isl_union_set *tmp;
  struct result_t result1, result2;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);

  node = insert_outer_shorter_sequence(node, idx1, idx2);
  // go to original, inner, longer sequence
  node = isl_schedule_node_child(node, idx1);
  node = isl_schedule_node_first_child(node);
  filters = isl_union_set_list_alloc(ctx, 2);
  node = get_filter_and_mupa(node, idx1, &result1, &filters);
  node = get_filter_and_mupa(node, idx2, &result2, &filters);
  mupa = isl_multi_union_pw_aff_union_add(result1.mupa, result2.mupa);
  node = isl_schedule_node_insert_sequence(node, filters);
  node = isl_schedule_node_insert_partial_schedule(node, mupa);
  return node;
}

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
  // printf("AFTER:\n%s\n\n", isl_schedule_node_to_str(node));
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
