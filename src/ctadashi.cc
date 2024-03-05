// Date: 2024, January
// Author: Emil VATAI, Riken R-CCS, HPAIS
//
// This file is the "C side" between the C and Python code of tadashi.

#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <isl/union_map.h>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include <isl/aff.h>
#include <isl/ast.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/union_set.h>
#include <isl/val.h>
#include <pet.h>

#include "codegen.h"
#include "legality.h"
#include "transformations.h"

extern "C" {

struct scop_info_t {
  pet_scop *scop;
  isl_union_map *dependency;
  isl_schedule_node *current_node;
  bool modified;
};

std::vector<struct scop_info_t> SCOP_INFO;
std::vector<std::string> STRINGS;

__isl_give isl_printer *get_scop(__isl_take isl_printer *p, pet_scop *scop,
                                 void *user) {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(sched);
  isl_schedule_free(sched);
  SCOP_INFO.push_back({scop, get_dependencies(scop), node, false});
  return p;
}

/******** scops constructor/descructor **********************/

int get_num_scops(char *input) { // Entry point

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");
  // pet_options_set_autodetect(ctx, 1);
  SCOP_INFO.clear();
  pet_transform_C_source(ctx, input, output, get_scop, NULL);
  fclose(output);
  return SCOP_INFO.size();
}

void free_scops() {
  if (SCOP_INFO.size() == 0)
    return;
  isl_set *set = pet_scop_get_context(SCOP_INFO[0].scop);
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_set_free(set);
  for (size_t i = 0; i < SCOP_INFO.size(); ++i) {
    isl_union_map_free(SCOP_INFO[i].dependency);
    pet_scop_free(SCOP_INFO[i].scop);
    isl_schedule_node_free(SCOP_INFO[i].current_node);
  }
  SCOP_INFO.clear();
  STRINGS.clear();
  isl_ctx_free(ctx);
}

/******** node info *****************************************/

int get_type(size_t scop_idx) {
  return isl_schedule_node_get_type(SCOP_INFO[scop_idx].current_node);
}

const char *get_type_str(size_t scop_idx) {
  enum isl_schedule_node_type type;
  type = isl_schedule_node_get_type(SCOP_INFO[scop_idx].current_node);
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
  return isl_schedule_node_n_children(SCOP_INFO[scop_idx].current_node);
}

const char *get_expr(size_t idx) {
  isl_schedule_node *node = SCOP_INFO[idx].current_node;
  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return "";
  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(node);
  const char *tmp = isl_multi_union_pw_aff_to_str(mupa);
  isl_multi_union_pw_aff_free(mupa);
  return tmp;
}

const char *get_dim_names(size_t scop_idx) {
  isl_schedule_node *node = SCOP_INFO[scop_idx].current_node;
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
  STRINGS.push_back(ss.str());
  return STRINGS.back().c_str();
}

const char *get_schedule_yaml(size_t scop_idx) {
  isl_schedule *sched = pet_scop_get_schedule(SCOP_INFO[scop_idx].scop);
  const char *ptr = isl_schedule_to_str(sched);
  isl_schedule_free(sched);
  return ptr;
}

/******** current node manipulation *************************/

void reset_root(size_t scop_idx) {
  SCOP_INFO[scop_idx].current_node =
      isl_schedule_node_root(SCOP_INFO[scop_idx].current_node);
}

void goto_parent(size_t scop_idx) {
  SCOP_INFO[scop_idx].current_node =
      isl_schedule_node_parent(SCOP_INFO[scop_idx].current_node);
}

void goto_child(size_t scop_idx, size_t child_idx) {
  SCOP_INFO[scop_idx].current_node =
      isl_schedule_node_child(SCOP_INFO[scop_idx].current_node, child_idx);
}

/******** transformations ***********************************/

int check_legality_after_transformation(size_t scop_idx) { return 0; }

int tile(size_t scop_idx, size_t tile_size) {
  scop_info_t *scop_info = &SCOP_INFO[scop_idx];
  isl_schedule_node *node = scop_info->current_node;
  scop_info->modified = true;
  node = tadashi_tile_1d(node, tile_size);
  return check_legality_after_transformation(scop_idx);
}

static __isl_give isl_printer *generate_code_callback(__isl_take isl_printer *p,
                                                      struct pet_scop *scop,
                                                      void *user) {
  isl_ctx *ctx;
  isl_schedule *sched;
  size_t *scop_idx = (size_t *)user;
  struct scop_info_t *scop_info = &SCOP_INFO[*scop_idx];

  if (!scop || !p)
    return isl_printer_free(p);
  ctx = isl_printer_get_ctx(p);
  sched = isl_schedule_node_get_schedule(scop_info->current_node);
  // p = isl_printer_print_schedule_node(p, scop_info->current_node);
  p = codegen(ctx, p, scop_info->scop, sched);
  pet_scop_free(scop);
  (*scop_idx)++;
  return p;
}

int generate_code(const char *input_path, const char *output_path) {
  int r;
  isl_ctx *ctx = isl_schedule_node_get_ctx(SCOP_INFO[0].current_node);
  size_t scop_idx = 0;

  //   isl_options_set_ast_print_macro_once(ctx, 1);
  //   pet_options_set_encapsulate_dynamic_control(ctx, 1);

  FILE *output_file = fopen(output_path, "w");
  r = pet_transform_C_source(ctx, input_path, output_file,
                             generate_code_callback, &scop_idx);
  fclose(output_file);
  return r;
}

// not needed? //

size_t depth(size_t scop_idx) {
  return isl_schedule_node_get_tree_depth(SCOP_INFO[scop_idx].current_node);
}

size_t child_position(size_t scop_idx) {
  return isl_schedule_node_get_child_position(SCOP_INFO[scop_idx].current_node);
}

} // extern "C"
