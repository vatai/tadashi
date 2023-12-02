#include <assert.h>
#include <isl/aff.h>
#include <isl/aff_type.h>
#include <isl/id.h>
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

  FILE *file;
  file = fopen("./examples/depnodep.c.0.tadashi.isl", "r");
  assert(file != 0);
  isl_union_map *umap = isl_union_map_read_from_file(ctx, file);
  isl_union_map_dump(umap);
  fclose(file);
  file = fopen("./examples/depnodep.c.0.tadashi.yaml", "r");
  assert(file != 0);
  isl_schedule *schedule = isl_schedule_read_from_file(ctx, file);
  // isl_schedule_dump(schedule);
  fclose(file);
  isl_schedule_free(schedule);
  isl_union_map_free(umap);

  isl_multi_union_pw_aff *mupa = isl_multi_union_pw_aff_read_from_str(
      ctx, "[N] -> L_1[{ S_0[i, j] -> [(j)] }, { S_0[i, j] -> [(i+j)] }, { "
           "S_0[i, j] -> [(j)] }]");
  enum isl_dim_type type = isl_dim_out;
  printf(">>>>%s\n", isl_multi_union_pw_aff_get_tuple_name(mupa, type));
  isl_size dim = isl_multi_union_pw_aff_dim(mupa, type);
  printf("DIM: %d\n", dim);
  for (size_t i = 0; i < dim; i++) {
    isl_union_pw_aff *upa = isl_multi_union_pw_aff_get_at(mupa, i);
    printf("upa: %s ", isl_union_pw_aff_to_str(upa));
    isl_pw_aff_list *lst = isl_union_pw_aff_get_pw_aff_list(upa);
    isl_pw_aff *pa = isl_pw_aff_list_get_at(lst, 0);
    isl_size d = isl_pw_aff_dim(pa, isl_dim_in);
    printf("(%d) dimname: %s, ", d, isl_pw_aff_get_dim_name(pa, isl_dim_in, 0));
    isl_id *id = isl_pw_aff_get_dim_id(pa, isl_dim_in, 0);
    printf("id: %s, ", isl_id_to_str(id));
    isl_id_free(id);
    printf("pa: %s\n", isl_pw_aff_to_str(pa));
    isl_pw_aff_free(pa);
    isl_pw_aff_list_free(lst);

    isl_union_pw_aff_free(upa);
  }
  printf("-----\n");
  isl_multi_union_pw_aff_free(mupa);

  isl_ctx_free(ctx);
  printf("Bye!\n");
}
