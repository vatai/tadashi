#include <assert.h>
#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/id.h>
#include <isl/map_type.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/space_type.h>
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

  isl_multi_union_pw_aff *mupa = isl_multi_union_pw_aff_read_from_str(
      ctx, "[N] -> L_1[{ S_0[i, j] -> [(j)] }, { S_0[i, j] -> [(i+j)] }, { "
           "S_0[i, j] -> [(j)] }]");
  enum isl_dim_type type = isl_dim_out;
  printf(">>>>%s\n", isl_multi_union_pw_aff_get_tuple_name(mupa, type));
  isl_union_set *domain = isl_multi_union_pw_aff_domain(mupa);
  printf("domain: %s\n", isl_union_set_to_str(domain));
  isl_size N = isl_union_set_n_set(domain);
  isl_set_list *slist = isl_union_set_get_set_list(domain);
  for (isl_size si = 0; si < N; si++) {
    isl_set *s = isl_set_list_get_at(slist, si);
    isl_size D = isl_set_dim(s, isl_dim_set);
    for (isl_size di = 0; di < D; di++) {
      printf("name: %s\n", isl_set_get_dim_name(s, isl_dim_set, di));
    }
    isl_set_free(s);
  }
  isl_set_list_free(slist);
  isl_union_set_free(domain);
  // isl_multi_union_pw_aff_free(mupa);
  printf("-----\n");

  isl_ctx_free(ctx);
  printf("Bye!\n");
}
