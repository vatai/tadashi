#include <cassert>
#include <iostream>

#include <isl/aff.h>
#include <isl/ctx.h>
#include <isl/map.h>
#include <isl/multi.h>
#include <isl/point.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/set.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>
#include <ostream>

isl_schedule *build_schedule_from_umap(__isl_take isl_union_set *domain,
                                       __isl_take isl_union_map *map);

int
main() {
  isl_ctx *ctx = isl_ctx_alloc();
  isl_union_set *domain = isl_union_set_read_from_str(
      ctx, "[p_0, p_1, p_2] -> { Stmt5[i0, i1, i2] : 0 <= i0 < p_0 and 0 <= i1 "
           "< p_2 and 0 <= i2 < p_1; Stmt2[i0, i1] : 0 <= i0 < p_0 and 0 <= i1 "
           "< p_1 }");
  isl_union_map *umap = isl_union_map_read_from_str(
      ctx, "[p_0, p_1, p_2] -> { Stmt2[i0, i1] -> [i0, 0, i1, 0]; Stmt5[i0, "
           "i1, i2] -> [i0, 1, i1, i2] }");
  isl_schedule *schedule = build_schedule_from_umap(domain, umap);
  isl_schedule_node *root;
  root = isl_schedule_get_root(schedule);

  std::cout << "========================================" << std::endl;
  std::cout << "========================================" << std::endl;
  std::cout << "RESULS: " << isl_schedule_node_to_str(root) << std::endl;
  std::cout << "DONE!" << std::endl;
  isl_schedule_free(schedule);
  isl_schedule_node_free(root);
  isl_ctx_free(ctx);
  return 0;
}
