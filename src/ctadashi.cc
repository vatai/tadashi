#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <isl/aff.h>
#include <isl/set.h>
#include <map>

#include <isl/ast.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/union_set.h>
#include <pet.h>
#include <sstream>
#include <string>
#include <vector>

extern "C" {

std::vector<pet_scop *> SCOPS;
std::vector<isl_schedule_node *> ROOTS;

__isl_give isl_printer *get_scop(__isl_take isl_printer *p, pet_scop *scop,
                                 void *user) {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(sched);
  isl_schedule_free(sched);
  SCOPS.push_back(scop);
  ROOTS.push_back(node);
  return p;
}

int get_num_scops(char *input) { // Entry point

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");
  // pet_options_set_autodetect(ctx, 1);
  pet_transform_C_source(ctx, input, output, get_scop, NULL);
  fclose(output);
  return SCOPS.size();
}

void free_scops() {
  if (SCOPS.size() == 0)
    return;
  isl_set *set = pet_scop_get_context(SCOPS[0]);
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_set_free(set);
  for (pet_scop *scop : SCOPS)
    pet_scop_free(scop);
  for (isl_schedule_node *root : ROOTS)
    isl_schedule_node_free(root);
  isl_ctx_free(ctx);
}

int get_type(size_t scop_idx) {
  return isl_schedule_node_get_type(ROOTS[scop_idx]);
}

const char *get_type_str(size_t scop_idx) {
  enum isl_schedule_node_type type;
  type = isl_schedule_node_get_type(ROOTS[scop_idx]);
  const char *type2str[11];

  type2str[isl_schedule_node_band] = "BND";
  type2str[isl_schedule_node_context] = "CTX";
  type2str[isl_schedule_node_domain] = "DMN";
  type2str[isl_schedule_node_expansion] = "EXP";
  type2str[isl_schedule_node_extension] = "EXT";
  type2str[isl_schedule_node_filter] = "FTR";
  type2str[isl_schedule_node_leaf] = "LF";
  type2str[isl_schedule_node_guard] = "GRD";
  type2str[isl_schedule_node_mark] = "MRK";
  type2str[isl_schedule_node_sequence] = "SEQ";
  type2str[isl_schedule_node_set] = "SET";
  return type2str[type];
}

size_t get_num_children(size_t scop_idx) {
  return isl_schedule_node_n_children(ROOTS[scop_idx]);
}

size_t depth(size_t scop_idx) {
  return isl_schedule_node_get_tree_depth(ROOTS[scop_idx]);
}

size_t child_position(size_t scop_idx) {
  return isl_schedule_node_get_child_position(ROOTS[scop_idx]);
}

void goto_parent(size_t scop_idx) {
  ROOTS[scop_idx] = isl_schedule_node_parent(ROOTS[scop_idx]);
}

void goto_child(size_t scop_idx, size_t child_idx) {
  ROOTS[scop_idx] = isl_schedule_node_child(ROOTS[scop_idx], child_idx);
}

const char *get_expr(size_t idx) {
  isl_schedule_node *node = ROOTS[idx];
  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return "";
  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(node);
  const char *tmp = isl_multi_union_pw_aff_to_str(mupa);
  isl_multi_union_pw_aff_free(mupa);
  return tmp;
}

const char *get_dim_names(size_t scop_idx) {
  isl_schedule_node *node = ROOTS[scop_idx];
  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return "";
  std::stringstream ss;
  const char *name;
  isl_multi_union_pw_aff *mupa;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  name = isl_multi_union_pw_aff_get_tuple_name(mupa, isl_dim_out);
  // TODO save name
  isl_union_set *domain = isl_multi_union_pw_aff_domain(mupa);
  isl_size num_sets = isl_union_set_n_set(domain);
  isl_set_list *slist = isl_union_set_get_set_list(domain);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    isl_set *set = isl_set_list_get_at(slist, set_idx);
    isl_size num_dims = isl_set_dim(set, isl_dim_set);
    for (isl_size di = 0; di < num_dims; di++) {
      ss << isl_set_get_dim_name(set, isl_dim_set, di);
      ss << "|";
    }
    ss << ";";
    isl_set_free(set);
  }
  isl_set_list_free(slist);
  isl_union_set_free(domain);
  return ss.str().c_str();
}

const char *get_schedule_yaml(size_t scop_idx) {
  isl_schedule *sched = pet_scop_get_schedule(SCOPS[scop_idx]);
  const char *ptr = isl_schedule_to_str(sched);
  isl_schedule_free(sched);
  return ptr;
}

} // extern "C"
