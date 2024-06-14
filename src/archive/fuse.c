#include <assert.h>

#include <stdio.h>

#include <isl/ast_build.h>
#include <isl/ctx.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <pet.h>

__isl_give isl_schedule_node *
complete_fuse(__isl_take isl_schedule_node *node) {
  // To merge all band node children of a sequence,
  //
  // take their partial schedules,
  //
  // intersect them with the corresponding filters and
  //
  // take the union.

  // Introduce a new band node on top of the sequence
  // using

  // If you want, you can then also delete the original band nodes,
  // but this is not strictly required since they will mostly be
  // ignored during AST generation.
  //// printf("%s\n", isl_schedule_node_to_str(node));
  isl_size num_children = isl_schedule_node_n_children(node);
  node = isl_schedule_node_first_child(node);
  isl_multi_union_pw_aff *mupa = NULL;
  for (isl_size i = 0; i < num_children; i++) {
    isl_union_set *filter;
    isl_multi_union_pw_aff *tmp;
    assert(isl_schedule_node_get_type(node) == isl_schedule_node_filter);
    filter = isl_schedule_node_filter_get_filter(node);
    node = isl_schedule_node_first_child(node);
    assert(isl_schedule_node_get_type(node) == isl_schedule_node_band);
    tmp = isl_schedule_node_band_get_partial_schedule(node);
    tmp = isl_multi_union_pw_aff_intersect_domain(tmp, filter);
    tmp = isl_multi_union_pw_aff_reset_tuple_id(tmp, isl_dim_out);
    if (mupa == NULL) {
      mupa = tmp;
    } else {
      mupa = isl_multi_union_pw_aff_union_add(mupa, tmp);
    }
    node = isl_schedule_node_delete(node);
    node = isl_schedule_node_parent(node);
    if (i == num_children - 1)
      node = isl_schedule_node_parent(node);
    else
      node = isl_schedule_node_next_sibling(node);
  }
  mupa = isl_multi_union_pw_aff_set_tuple_name(mupa, isl_dim_out, "Fused");
  /* isl_schedule *sched; */
  /* sched = isl_schedule_node_get_schedule(node); */
  /* sched = isl_schedule_insert_partial_schedule(sched, mupa); */
  /* node = isl_schedule_get_root(sched); */
  node = isl_schedule_node_insert_partial_schedule(node, mupa);
  //// printf("%s\n", isl_schedule_node_to_str(node));
  return node;
}

char fused_str[] =
    "domain: \"[N] -> { S_0[i, j, k] : 0 < i < N and 0 <= j < N and 0 <= k < "
    "N; S_1[i, j, k] : 0 < i < N and 0 <= j < N and 0 <= k < N; S_2[i, j, k] : "
    "0 < i < N and 0 <= j < N and 0 <= k < N }\"\nchild:\n  schedule: \"[N] -> "
    "L_0[{ S_0[i, j, k] -> [(i)]; S_1[i, j, k] -> [(i)]; S_2[i, j, k] -> [(i)] "
    "}]\"\n  child:\n    schedule: \"[N] -> L_1[{ S_0[i, j, k] -> [(j)]; "
    "S_1[i, j, k] -> [(j)]; S_2[i, j, k] -> [(j)] }]\"\n    child:\n      # "
    "YOU ARE HERE\n      schedule: \"[N] -> Fused[{ S_1[i, j, k] -> [(k)]; "
    "S_2[i, j, k] -> [(k)]; S_0[i, j, k] -> [(k)] }]\"\n      child:\n        "
    "sequence:\n        - filter: \"[N] -> { S_0[i, j, k] }\"\n        - "
    "filter: \"[N] -> { S_1[i, j, k] }\"\n        - filter: \"[N] -> { S_2[i, "
    "j, k] }\"\n";

char unfused_str[] =
    "domain: \"[N] -> { S_0[i, j, k] : 0 < i < N and 0 <= j < N and 0 <= k < "
    "N; S_1[i, j, k] : 0 < i < N and 0 <= j < N and 0 <= k < N; S_2[i, j, k] : "
    "0 < i < N and 0 <= j < N and 0 <= k < N }\"\nchild:\n  schedule: \"[N] -> "
    "L_0[{ S_0[i, j, k] -> [(i)]; S_1[i, j, k] -> [(i)]; S_2[i, j, k] -> [(i)] "
    "}]\"\n  child:\n    schedule: \"[N] -> L_1[{ S_0[i, j, k] -> [(j)]; "
    "S_1[i, j, k] -> [(j)]; S_2[i, j, k] -> [(j)] }]\"\n    child:\n      # "
    "YOU ARE HERE\n      sequence:\n      - filter: \"[N] -> { S_0[i, j, k] "
    "}\"\n        child:\n          schedule: \"[N] -> L_2[{ S_0[i, j, k] -> "
    "[(k)] }]\"\n      - filter: \"[N] -> { S_1[i, j, k] }\"\n        child:\n "
    "         schedule: \"[N] -> L_3[{ S_1[i, j, k] -> [(k)] }]\"\n      - "
    "filter: \"[N] -> { S_2[i, j, k] }\"\n        child:\n          schedule: "
    "\"[N] -> L_4[{ S_2[i, j, k] -> [(k)] }]\"\n";

static __isl_give isl_printer *scop_callback(__isl_take isl_printer *p,
                                             pet_scop *scop, void *user);

int main(int argc, char *argv[]) {

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  char *node_str = unfused_str;
  // node_str = fused_str; /// UNCOMMENT ME!!!!!!!!!!!
  isl_schedule *sched = isl_schedule_read_from_str(ctx, node_str);
  isl_schedule_node *node = isl_schedule_get_root(sched);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  node = isl_schedule_node_first_child(node);
  if (node_str == unfused_str)
    node = complete_fuse(node);
  isl_schedule_node_dump(node);

  isl_ast_build *build = isl_ast_build_alloc(ctx);
  isl_ast_node *ast_node = isl_ast_build_node_from_schedule(build, sched);
  isl_ast_print_options *print_options = isl_ast_print_options_alloc(ctx);
  isl_printer *p = isl_printer_to_str(ctx);
  p = isl_ast_node_print(ast_node, p, print_options);
  printf("Code:\n%s\n", isl_printer_get_str(p));

  return 0;
}
