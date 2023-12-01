#include <assert.h>
#include <isl/ctx.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/union_map.h>
#include <isl/union_map_type.h>
#include <isl/union_set.h>
#include <stdio.h>

#include <pet.h>

#include <isl/set.h>

int main(int argc, char *argv[]) {
  isl_ctx *ctx = isl_ctx_alloc();

  printf("Hello\n");

  FILE *file;
  file = fopen("./examples/dotprod.c.0.tadashi.isl", "r");
  isl_union_map *umap = isl_union_map_read_from_file(ctx, file);
  isl_union_map_dump(umap);
  fclose(file);
  file = fopen("./examples/dotprod.c.0.tadashi.yaml", "r");
  isl_schedule *schedule = isl_schedule_read_from_file(ctx, file);
  isl_schedule_dump(schedule);
  fclose(file);
  isl_schedule_node *n = isl_schedule_get_root(schedule);
  n = isl_schedule_node_child(n, 0);
  assert(isl_schedule_node_get_type(n) == isl_schedule_node_sequence);
  isl_schedule_node *t = isl_schedule_node_get_child(n, 2);
  n = isl_schedule_node_child(n, 1);
  assert(isl_schedule_node_get_type(n) == isl_schedule_node_filter);
  isl_schedule_node_dump(n);
  isl_union_set *nf = isl_schedule_node_filter_get_filter(n);
  isl_union_set *tf = isl_schedule_node_filter_get_filter(t);
  isl_union_set_dump(nf);
  isl_union_set_dump(tf);

  umap = isl_union_map_intersect_domain(umap, nf);
  isl_union_map_dump(umap);
  umap = isl_union_map_intersect_range(umap, tf);
  isl_union_map_dump(umap);
  isl_union_set *delta = isl_union_map_deltas(umap);
  isl_union_set_dump(delta);

  // isl_union_set_free(nf);
  // isl_union_set_free(tf);
  isl_union_set_free(delta);
  isl_schedule_node_free(n);
  isl_schedule_node_free(t);
  isl_schedule_free(schedule);
  // isl_union_map_free(umap);
  printf("Bye!\n");
  isl_ctx_free(ctx);
}

void f() {
  // const char *testName =
  //     ::testing::UnitTest::GetInstance()->current_test_info()->name();
  // FILE *output_file = fopen(opt->output_file_path, "w");
  // r = pet_transform_C_source(ctx, opt->source_file_path, output_file,
  //                            &foreach_scop_callback, &counter);
  // fprintf(stderr, "Number of scops: %lu\n", counter);
  // fclose(output_file);
}
