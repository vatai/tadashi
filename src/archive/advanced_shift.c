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

__isl_give isl_union_pw_aff *proc_upa(isl_union_pw_aff *upa) {
  isl_ctx *ctx;
  isl_union_set *domain;
  isl_space *upa_space;
  isl_val *val;
  isl_pw_aff_list *pal;
  isl_pw_aff *pa;
  isl_set_list *slist;
  isl_size num_sets;
  isl_set *set;
  ctx = isl_union_pw_aff_get_ctx(upa);
  domain = isl_union_pw_aff_domain(upa);
  printf("domain: %s\n", isl_union_set_to_str(domain));
  slist = isl_union_set_get_set_list(domain);
  num_sets = isl_set_list_n_set(slist);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    set = isl_set_list_get_at(slist, set_idx);
    printf("set[%d] = %s\n", set_idx, isl_set_to_str(set));
  }
  val = isl_val_int_from_si(ctx, 0);
  upa = isl_union_pw_aff_val_on_domain(domain, val);
  printf("zero upa: %s\n", isl_union_pw_aff_to_str(upa));
  set = isl_set_list_get_at(slist, 0);
  val = isl_val_int_from_si(ctx, 42);
  pa = isl_pw_aff_val_on_domain(set, val);
  printf("pa: %s\n", isl_pw_aff_to_str(pa));

  printf("transformed upa: %s\n", isl_union_pw_aff_to_str(upa));
  return upa;

  // val = isl_val_int_from_si(ctx, 42);
  pal = isl_union_pw_aff_get_pw_aff_list(upa);
  pa = isl_pw_aff_list_get_at(pal, 0);
  printf("pa: %s\n", isl_pw_aff_to_str(pa));
  isl_pw_aff_free(pa);
  isl_pw_aff_list_free(pal);
  pa = isl_union_pw_aff_extract_pw_aff(upa, upa_space); //// TODO
  printf("pa (extracted): %s\n", isl_pw_aff_to_str(pa));
  // isl_union_pw_aff_pw_aff_on_domain(domain, pa);
  // pa = isl_pw_aff_val_on_domain(pa_domain, val);
  // upa = isl_union_pw_aff_add_pw_aff(upa, pa);
  printf("upa: %s\n", isl_union_pw_aff_to_str(upa));
  // upa = isl_union_pw_aff_param_on_domain_id(domain, id);
  return upa;
}

__isl_give isl_multi_union_pw_aff *brutus(__isl_keep isl_schedule_node *node) {
  int upal_idx;
  isl_ctx *ctx;
  isl_multi_union_pw_aff *mupa;
  isl_size upal_size;
  isl_space *space;
  isl_union_pw_aff *upa;
  isl_union_pw_aff_list *upal, *upal_new;
  ctx = isl_schedule_node_get_ctx(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  printf("mupa (node): %s\n", isl_multi_union_pw_aff_to_str(mupa));

  space = isl_schedule_node_band_get_space(node);
  printf("space (band node): %s\n", isl_space_to_str(space));

  upal = isl_multi_union_pw_aff_get_list(mupa);
  upal_size = isl_union_pw_aff_list_size(upal);
  printf("len(upal)=%d\n", upal_size);
  isl_multi_union_pw_aff_free(mupa);
  upal_new = isl_union_pw_aff_list_alloc(ctx, upal_size);
  for (upal_idx = 0; upal_idx < upal_size; upal_idx++) {
    upa = isl_union_pw_aff_list_get_at(upal, upal_idx);
    printf("upal[%d]=%s\n", upal_idx, isl_union_pw_aff_to_str(upa));
    upa = proc_upa(upa);
    upal_new = isl_union_pw_aff_list_add(upal_new, upa);
  }
  mupa = isl_multi_union_pw_aff_from_union_pw_aff_list(space, upal_new);
  isl_union_pw_aff_list_free(upal);
  return mupa;
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
