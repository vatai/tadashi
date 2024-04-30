#include <assert.h>
#include <isl/local_space.h>
#include <stdio.h>

#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/id_type.h>
#include <isl/map.h>
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

  file = fopen("/home/vatai/code/tadashi/build/_deps/polybench-src/"
               "linear-algebra/blas/gemm/"
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

__isl_give isl_union_pw_aff *proc_upa2(isl_union_pw_aff *upa, int idx,
                                       long const_val) {
  isl_ctx *ctx;
  isl_union_set *upa_domain;
  isl_space *upa_space;
  isl_val *val;
  isl_pw_aff *pa;
  isl_set_list *pa_domains;
  isl_size num_sets;
  isl_set *set;

  ctx = isl_union_pw_aff_get_ctx(upa);
  upa_space = isl_union_pw_aff_get_space(upa);
  upa_domain = isl_union_pw_aff_domain(upa); // takes upa
  pa_domains = isl_union_set_get_set_list(upa_domain);
  upa = isl_union_pw_aff_empty_space(upa_space);
  num_sets = isl_set_list_n_set(pa_domains);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    val = isl_val_int_from_si(ctx, const_val);
    set = isl_set_list_get_at(pa_domains, set_idx);
    pa = isl_pw_aff_val_on_domain(set, val);
    upa = isl_union_pw_aff_add_pw_aff(upa, pa);
  }
  pa_domains = isl_set_list_free(pa_domains);
  return upa;
}

__isl_give isl_multi_union_pw_aff *brutus2(__isl_keep isl_schedule_node *node,
                                           int idx, long const_val) {
  int mupa_idx = 0;
  isl_ctx *ctx;
  isl_multi_union_pw_aff *mupa;
  isl_size mupa_dim;
  isl_union_pw_aff *upa;
  isl_id *id;
  ctx = isl_schedule_node_get_ctx(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  id = isl_multi_union_pw_aff_get_tuple_id(mupa, isl_dim_out);
  printf("tuple id: %s\n", isl_id_to_str(id));
  mupa_dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_out);
  assert(mupa_dim == 1);
  upa = isl_multi_union_pw_aff_get_at(mupa, mupa_idx);
  printf("upa: %s\n", isl_union_pw_aff_to_str(upa));
  upa = proc_upa2(upa, idx, const_val);
  printf("upa: %s\n", isl_union_pw_aff_to_str(upa));
  //
  mupa = isl_multi_union_pw_aff_from_union_pw_aff(upa);
  mupa = isl_multi_union_pw_aff_set_tuple_id(mupa, isl_dim_out, id);
  printf("mupa: %s\n", isl_multi_union_pw_aff_to_str(mupa));
  return mupa;
}

__isl_give isl_schedule_node *
shift_and_print(__isl_take isl_schedule_node *node,
                __isl_take isl_multi_union_pw_aff *mupa) {

  node = isl_schedule_node_band_shift(node, mupa);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  printf("mupa (after shift): %s\n", isl_multi_union_pw_aff_to_str(mupa));
  mupa = isl_multi_union_pw_aff_free(mupa);
  return node;
}

int main() {
  printf("Hello\n");
  isl_ctx *ctx = isl_ctx_alloc();
  isl_schedule_node *node = navigate_to_the_node(ctx);
  isl_multi_union_pw_aff *mupa;
  mupa = brutus2(node, 1, 42);
  node = shift_and_print(node, mupa);
  node = isl_schedule_node_free(node);
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
