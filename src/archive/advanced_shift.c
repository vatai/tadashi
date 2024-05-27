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

__isl_give isl_pw_aff *pa_val(__isl_take isl_set *set, long val) {
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_val *v = isl_val_int_from_si(ctx, val);
  return isl_pw_aff_val_on_domain(set, v);
}

__isl_give isl_pw_aff *id_pa(__isl_take isl_set *set, long id_idx) {
  isl_space *space = isl_set_get_space(set);
  set = isl_set_free(set);
  isl_size ndims = isl_space_dim(space, isl_dim_out);
  space = isl_space_add_dims(space, isl_dim_in, ndims);
  for (int i = 0; i < ndims; ++i) {
    isl_id *id = isl_space_get_dim_id(space, isl_dim_out, i);
    space = isl_space_set_dim_id(space, isl_dim_in, i, id);
  }
  const char *name = isl_space_get_tuple_name(space, isl_dim_out);
  space = isl_space_set_tuple_name(space, isl_dim_in, name);
  isl_multi_aff *ma = isl_multi_aff_identity(space);
  isl_aff *aff = isl_multi_aff_get_at(ma, id_idx);
  ma = isl_multi_aff_free(ma);
  return isl_pw_aff_from_aff(aff);
}

__isl_give isl_schedule_node *shift_partial(
    __isl_keep isl_schedule_node *node,
    __isl_give isl_pw_aff *(*fn)(__isl_take isl_set *set, long const_val),
    int idx, long const_val) {
  isl_multi_union_pw_aff *mupa;
  isl_union_pw_aff *upa;
  isl_union_set *upa_domain;
  isl_set_list *pa_domains;
  isl_id *id;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  id = isl_multi_union_pw_aff_get_tuple_id(mupa, isl_dim_out);
  isl_size mupa_dim = isl_multi_union_pw_aff_dim(mupa, isl_dim_out);
  assert(mupa_dim == 1);
  upa = isl_multi_union_pw_aff_get_at(mupa, 0);
  mupa = isl_multi_union_pw_aff_free(mupa);
  upa_domain = isl_union_pw_aff_domain(upa); // takes upa
  pa_domains = isl_union_set_get_set_list(upa_domain);
  upa_domain = isl_union_set_free(upa_domain);
  upa = isl_union_pw_aff_empty_ctx(ctx);
  isl_size num_sets = isl_set_list_n_set(pa_domains);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    isl_set *set = isl_set_list_get_at(pa_domains, set_idx);
    isl_pw_aff *pa = ((idx == set_idx) ? fn(set, const_val) : pa_val(set, 0));
    upa = isl_union_pw_aff_add_pw_aff(upa, pa);
  }
  pa_domains = isl_set_list_free(pa_domains);
  printf("upa: %s\n", isl_union_pw_aff_to_str(upa));
  mupa = isl_multi_union_pw_aff_from_union_pw_aff(upa);
  mupa = isl_multi_union_pw_aff_set_tuple_id(mupa, isl_dim_out, id);
  printf("mupa: %s\n", isl_multi_union_pw_aff_to_str(mupa));
  return isl_schedule_node_band_shift(node, mupa);
}

__isl_give isl_schedule_node *shift_var(__isl_take isl_schedule_node *node,
                                        long var_idx) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  isl_multi_union_pw_aff *mupa;
  isl_union_pw_aff *upa;
  isl_id *id;
  isl_union_set *domain;
  isl_union_pw_multi_aff *upma;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  upa = isl_multi_union_pw_aff_get_at(mupa, 0);
  id = isl_multi_union_pw_aff_get_tuple_id(mupa, isl_dim_out);
  mupa = isl_multi_union_pw_aff_free(mupa);
  domain = isl_union_pw_aff_domain(upa);
  upma = isl_union_set_identity_union_pw_multi_aff(domain);
  upa = isl_union_pw_multi_aff_get_union_pw_aff(upma, var_idx);
  upma = isl_union_pw_multi_aff_free(upma);
  mupa = isl_multi_union_pw_aff_from_union_pw_aff(upa);
  mupa = isl_multi_union_pw_aff_set_tuple_id(mupa, isl_dim_out, id);
  node = isl_schedule_node_band_shift(node, mupa);
  return node;
}

__isl_give isl_schedule_node *shift_val(__isl_take isl_schedule_node *node,
                                        long val) {
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  isl_val *v = isl_val_int_from_si(ctx, val);
  isl_multi_union_pw_aff *mupa;
  isl_union_pw_aff *upa;
  isl_union_set *domain;
  isl_id *id;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  id = isl_multi_union_pw_aff_get_tuple_id(mupa, isl_dim_out);
  upa = isl_multi_union_pw_aff_get_at(mupa, 0);
  mupa = isl_multi_union_pw_aff_free(mupa);
  domain = isl_union_pw_aff_domain(upa);
  upa = isl_union_pw_aff_val_on_domain(domain, v);
  mupa = isl_multi_union_pw_aff_from_union_pw_aff(upa);
  mupa = isl_multi_union_pw_aff_set_tuple_id(mupa, isl_dim_out, id);
  node = isl_schedule_node_band_shift(node, mupa);
  return node;
}

int main() {
  printf("Hello\n");
  isl_ctx *ctx = isl_ctx_alloc();
  isl_schedule_node *node = navigate_to_the_node(ctx);
  isl_multi_union_pw_aff *mupa;

  // node = shift_partial(node, id_pa, 1, 0);

  long coeff = 1;
  long var_idx = 0;
  node = shift_var(node, var_idx);
  long val = 42;
  node = shift_val(node, val);

  mupa = isl_schedule_node_band_get_partial_schedule(node);
  printf("mupa (after shift): %s\n", isl_multi_union_pw_aff_to_str(mupa));
  mupa = isl_multi_union_pw_aff_free(mupa);

  node = isl_schedule_node_free(node);
  isl_ctx_free(ctx);
  printf("Bye!\n");
  return 0;
}
