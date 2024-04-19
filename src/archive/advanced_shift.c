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

__isl_give isl_schedule_node *navigate_to_the_node(isl_ctx *ctx) {
  FILE *file;
  // create file with: C_INCLUDE_PATH=./build/_deps/polybench-src/utilities
  // ./build/tadashi -s tadashi.yaml
  // build/_deps/polybench-src/linear-algebra/blas/gemm/gemm.c

  file = fopen("build/_deps/polybench-src/linear-algebra/blas/gemm/"
               "gemm.c.0.tadashi.yaml",
               "r");
  assert(file != 0);
  isl_schedule *schedule = isl_schedule_read_from_file(ctx, file);
  fclose(file);
  isl_schedule_node *node = isl_schedule_get_root(schedule);
  isl_schedule_free(schedule);
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
  return node;
}

void the_void() {
  isl_space *space;
  isl_union_set *domain;
  char *mupa_str;
  isl_multi_aff *ma;
  isl_val *val;
  isl_set_list *slist;
  isl_set *set;
  isl_multi_val *mv;
  isl_schedule_node *node;
  isl_multi_union_pw_aff *mupa;

  // mupa = isl_multi_union_pw_aff_zero(isl_space_copy(space));
  // FAILS WITH: Expectin 0D space
  // printf("mupa1: %s\n", isl_multi_union_pw_aff_to_str(mupa));

  space = isl_multi_union_pw_aff_get_domain_space(
      isl_multi_union_pw_aff_copy(mupa));
  printf("space (domain space): %s\n", isl_space_to_str(space));
  // mupa = isl_multi_union_pw_aff_zero(space);
  // printf("mupa (zero): %s\n", isl_multi_union_pw_aff_to_str(mupa));
  // isl_aff.c:8768: expecting proper set space

  mupa = isl_multi_union_pw_aff_from_range(isl_multi_union_pw_aff_copy(mupa));
  printf("mupa (range): %s\n", isl_multi_union_pw_aff_to_str(mupa));

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
  isl_union_set_free(domain);
}

__isl_give isl_multi_union_pw_aff *brutus(__isl_keep isl_schedule_node *node) {
  isl_space *space;
  isl_multi_union_pw_aff *mupa;
  isl_union_pw_aff_list *upal, *upal_new;
  isl_union_pw_aff *upa;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  printf("mupa (node): %s\n", isl_multi_union_pw_aff_to_str(mupa));

  space = isl_schedule_node_band_get_space(node);
  printf("space (band node): %s\n", isl_space_to_str(space));

  upal = isl_multi_union_pw_aff_get_list(mupa);
  printf("len(upal)=%d\n", isl_union_pw_aff_list_size(upal));
  upa = isl_union_pw_aff_list_get_at(upal, 0);
  printf("upa (at 0): %s\n", isl_union_pw_aff_to_str(upa));
  //////////////
  isl_union_pw_aff_free(upa);
  isl_union_pw_aff_list_free(upal);
  isl_space_free(space);
  return mupa;
  /////////////
  isl_space *space0 = isl_union_pw_aff_get_space(isl_union_pw_aff_copy(upa));
  printf("space0: %s\n", isl_space_to_str(space));
  isl_pw_aff_list *pal =
      isl_union_pw_aff_get_pw_aff_list(isl_union_pw_aff_copy(upa));
  size_t size = isl_pw_aff_list_size(pal);
  for (size_t i = 0; i < size; ++i) {
    printf("[%d] %s\n", i, isl_pw_aff_to_str(isl_pw_aff_list_get_at(pal, i)));
    printf("Hi\n");
  }
  upa = isl_union_pw_aff_empty_space(space0);
  upal_new = isl_union_pw_aff_list_from_union_pw_aff(upa);
  printf("upa (empty space): %s\n", isl_union_pw_aff_to_str(upa));
  mupa = isl_multi_union_pw_aff_from_union_pw_aff_list(space, upal_new);
  printf("mupa (from list): %s\n", isl_multi_union_pw_aff_to_str(mupa));
}

__isl_give isl_schedule_node *
shift_and_print(__isl_take isl_schedule_node *node,
                __isl_take isl_multi_union_pw_aff *mupa) {

  node = isl_schedule_node_band_shift(node, mupa);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  printf("mupa (after shift): %s\n", isl_multi_union_pw_aff_to_str(mupa));
  isl_multi_union_pw_aff_free(mupa);
  return node;
}

int main() {
  printf("Hello\n");
  isl_ctx *ctx = isl_ctx_alloc();
  isl_schedule_node *node = navigate_to_the_node(ctx);
  isl_multi_union_pw_aff *mupa;
  mupa = brutus(node);
  node = shift_and_print(node, mupa);
  isl_schedule_node_free(node);
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
