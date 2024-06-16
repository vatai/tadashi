#include <assert.h>
#include <isl/aff.h>
#include <isl/id.h>
#include <isl/mat.h>
#include <isl/set.h>
#include <isl/space.h>
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
  isl_mat *eq = isl_mat_alloc(ctx, 0, 5);
  isl_mat *ineq = isl_mat_alloc(ctx, 2, 5);
  ineq = isl_mat_set_element_si(ineq, 0, 0, 2);  // p0
  ineq = isl_mat_set_element_si(ineq, 0, 1, 0);  // i0
  ineq = isl_mat_set_element_si(ineq, 0, 2, 5);  // i1
  ineq = isl_mat_set_element_si(ineq, 0, 3, 7);  // e0
  ineq = isl_mat_set_element_si(ineq, 0, 4, 11); // const
  // and
  ineq = isl_mat_set_element_si(ineq, 1, 0, 21);  // p0
  ineq = isl_mat_set_element_si(ineq, 1, 1, 31);  // i0
  ineq = isl_mat_set_element_si(ineq, 1, 2, 51);  // i1
  ineq = isl_mat_set_element_si(ineq, 1, 3, 71);  // e0
  ineq = isl_mat_set_element_si(ineq, 1, 4, 111); // const
  isl_space *space = isl_space_set_alloc(ctx, 1, 2);
  isl_basic_set *bset = isl_basic_set_from_constraint_matrices(
      space, eq, ineq, isl_dim_param, isl_dim_set, isl_dim_div, isl_dim_cst);
  isl_basic_set_dump(bset);
  bset = isl_basic_set_free(bset);
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
