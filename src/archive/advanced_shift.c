#include <assert.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/id_type.h>
#include <isl/map_type.h>
#include <isl/multi.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/space.h>
#include <isl/space_type.h>
#include <isl/union_map.h>
#include <isl/union_map_type.h>
#include <isl/union_set.h>
#include <isl/val.h>

int main() {
  printf("Hello\n");
  isl_ctx *ctx = isl_ctx_alloc();

  FILE *file;
  // create file with:
  // C_INCLUDE_PATH=./build/_deps/polybench-src/utilities
  // ./build/tadashi -s tadashi.yaml
  // build/_deps/polybench-src/linear-algebra/blas/gemm/gemm.c

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
  node = isl_schedule_node_band_scale(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, 60))));
  node = isl_schedule_node_band_scale_down(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, 3))));

  isl_space *space;
  isl_union_set *domain;
  char *mupa_str;
  isl_multi_union_pw_aff *mupa;
  isl_multi_aff *ma;
  isl_val *val;
  isl_set_list *slist;
  isl_set *set;
  isl_multi_val *mv;

  mupa = isl_schedule_node_band_get_partial_schedule(node);
  printf("mupa (node): %s\n", isl_multi_union_pw_aff_to_str(mupa));

  space = isl_multi_union_pw_aff_get_domain_space(mupa);
  mupa = isl_multi_union_pw_aff_zero(space);
  printf("mupa (zero): %s\n", isl_multi_union_pw_aff_to_str(mupa));
  space = isl_schedule_node_band_get_space(node);
  printf("space (band node): %s\n", isl_space_to_str(space));
  // mupa = isl_multi_union_pw_aff_zero(isl_space_copy(space));
  // FAILS WITH: Expectin 0D space
  // printf("mupa1: %s\n", isl_multi_union_pw_aff_to_str(mupa));

  // ma = isl_multi_aff_identity_on_domain_space(space);
  // printf("ma: %s\n", isl_multi_aff_to_str(ma));
  // isl_multi_aff_free(ma);
  domain = isl_schedule_node_get_domain(node);
  printf("domain: %s\n", isl_union_set_to_str(domain));

  mv = isl_multi_val_zero(isl_space_copy(space));
  printf("mv: %s\n", isl_multi_val_to_str(mv));
  mupa = isl_multi_union_pw_aff_multi_val_on_domain(isl_union_set_copy(domain),
                                                    mv);
  printf("mupa1: %s\n", isl_multi_union_pw_aff_to_str(mupa));

  // isl_multi_val_free(mv);
  isl_space_free(space);
  // mupa =
  // isl_multi_union_pw_aff_multi_aff_on_domain(isl_union_set_copy(domain), ma);
  // FAILS WITH: "expecting parametric expression
  // printf("mupa1: %s\n", isl_multi_union_pw_aff_to_str(mupa));

  space = isl_union_set_get_space(domain);
  printf("space (domain): %s\n", isl_space_to_str(space));

  // mupa = isl_multi_union_pw_aff_zero(isl_space_copy(space));
  // FAILS WITH: expecting proper set space
  // printf("mupa1: %s\n", isl_multi_union_pw_aff_to_str(mupa));

  /* slist = isl_union_set_get_set_list(domain); */
  /* set = isl_set_list_get_at(slist, 0); */
  /* printf("set: %s\n", isl_set_to_str(set)); */
  /* printf("dim name: %s\n", isl_set_get_dim_name(set, isl_dim_set, 0)); */
  /* printf("tuple name: %s\n", isl_set_get_tuple_name(set)); */

  /* space = isl_set_get_space(set); */
  /* printf("space (set): %s\n", isl_space_to_str(space)); */
  /* isl_set_free(set); */
  /* isl_set_list_free(slist); */

  // mupa = isl_multi_union_pw_aff_zero(isl_space_copy(space));
  // FAILS WITH: Expectin 0D space
  // printf("mupa1: %s\n", isl_multi_union_pw_aff_to_str(mupa));
  isl_space_free(space);

  // space: [this] -> L_andthis[maybe_this]
  mupa_str = "[ni, nj] -> L_1[{ S_3[i,j] -> [(300)]; S_2[i,j]->[(400)] } ]";
  // mupa = isl_multi_union_pw_aff_read_from_str(ctx, mupa_str);
  // mupa = isl_multi_union_pw_aff_multi_val_on_domain(domain, mv);
  printf("mupa0: %s\n", isl_multi_union_pw_aff_to_str(mupa));
  /* isl_multi_union_pw_aff_free(mupa); */
  node = isl_schedule_node_band_shift(node, mupa);

  printf("\n\nSHIFT:\n%s\n\n", isl_schedule_node_to_str(node));

  isl_schedule_node_free(node);
  isl_union_set_free(domain);
  isl_schedule_free(schedule);
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
