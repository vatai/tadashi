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

  isl_schedule *schedule = isl_schedule_from_domain(
      isl_union_set_read_from_str(ctx, "[N] -> {S_0[i] : 0 <= i < N;"         //
                                       "S_1[i, j] : 0 < i < N and 0 < j < N;" //
                                       "S_2[i, j] : 0 < i < N and 0 < j < N; "
                                       "S_3[i] : 0 <= i < N }"));
  isl_schedule_node *node = isl_schedule_get_root(schedule);

  node = isl_schedule_node_first_child(node);
  isl_union_set_list *flist = isl_union_set_list_from_union_set(
      isl_union_set_read_from_str(ctx, "[N] -> { S_0[i] }"));
  flist = isl_union_set_list_insert(
      flist, isl_union_set_list_size(flist),
      isl_union_set_read_from_str(ctx, "[N]->{S_1[i,j]; S_2[i,j] }"));
  flist = isl_union_set_list_insert(
      flist, isl_union_set_list_size(flist),
      isl_union_set_read_from_str(ctx, "[N]->{S_3[i,j] }"));
  node = isl_schedule_node_insert_sequence(node, flist);

  node = isl_schedule_node_child(node, 0);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_read_from_str(
                ctx, "[N] -> L_0[{ S_0[i] -> [i]}]"));

  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_insert_mark(node, isl_id_read_from_str(ctx, "foo"));
  node = isl_schedule_node_parent(node);

  node = isl_schedule_node_parent(node);

  node = isl_schedule_node_next_sibling(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_read_from_str(
                ctx, "[N] -> L_1[{ S_1[i,j] -> [i]; S_2[i,j] -> [i] }]"));
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_read_from_str(
                ctx, "[N] -> L_2[{ S_1[i,j] -> [j]; S_2[i,j] -> [j] }]"));
  flist = isl_union_set_list_from_union_set(
      isl_union_set_read_from_str(ctx, "[N] -> {S_1[i,j]}"));
  flist = isl_union_set_list_insert(
      flist, isl_union_set_list_size(flist),
      isl_union_set_read_from_str(ctx, "[N] -> {S_2[i,j]}"));
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_insert_sequence(node, flist);
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_band_sink(node); // Try commenting this
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);

  node = isl_schedule_node_next_sibling(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_insert_partial_schedule(
      node, isl_multi_union_pw_aff_read_from_str(
                ctx, "[N] -> L_3[{ S_3[i] -> [i]}]"));

  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_order_before(
      node, isl_union_set_read_from_str(
                ctx, "[N]->{ S_3[i] : 0 <= i < floor(N/2) }"));
  node = isl_schedule_node_parent(node);
  node = isl_schedule_node_parent(node);
  // node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_parent(node);
  // node = isl_schedule_node_parent(node);
  isl_schedule_node_dump(node);
  node = isl_schedule_node_order_before(
      node, isl_union_set_read_from_str(ctx, "[N]->{S_0[i] : 0 <= i < N/2}"));

  isl_schedule_node_dump(node);
  isl_schedule_node_free(node);
  isl_schedule_free(schedule);

  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
