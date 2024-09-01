// Date: 2024, January
// Author: Emil VATAI, Riken R-CCS, HPAIS
//
// This file is the "C side" between the C and Python code of tadashi.

#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <isl/aff_type.h>
#include <isl/space_type.h>
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
#include <isl/set.h>
#include <isl/space.h>
#include <isl/union_map.h>
#include <isl/union_set.h>
#include <isl/val.h>

#include "codegen.h"
#include "legality.h"
#include "transformations.h"

extern "C" {
#include "ctadashi.h"

std::vector<struct scop_info_t> SCOP_INFO;

std::vector<std::string> STRINGS;

/******** scops constructor/descructor **********************/

__isl_give isl_printer *
get_scop_callback(__isl_take isl_printer *p, pet_scop *scop, void *user) {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(sched);
  isl_schedule_free(sched);
  isl_union_map *dep = get_dependencies(scop);

  SCOP_INFO.push_back({.scop = scop,
                       .dependency = dep,
                       .current_node = node,
                       .tmp_node = NULL,
                       .modified = false});
  return p;
}

int
get_num_scops(char *input) { // Entry point

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");
  // pet_options_set_autodetect(ctx, 1);
  // pet_options_set_signed_overflow(ctx, 1);
  // pet_options_set_encapsulate_dynamic_control(ctx, 1);
  SCOP_INFO.clear();
  pet_transform_C_source(ctx, input, output, get_scop_callback, NULL);
  fclose(output);
  return SCOP_INFO.size();
}

void
free_scops() {
  if (SCOP_INFO.size() == 0)
    return;
  isl_set *set = pet_scop_get_context(SCOP_INFO[0].scop);
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_set_free(set);
  for (size_t i = 0; i < SCOP_INFO.size(); ++i) {
    scop_info_t *si = &SCOP_INFO[i];
    isl_union_map_free(si->dependency);
    pet_scop_free(si->scop);
    isl_schedule_node_free(si->current_node);
    if (si->tmp_node != NULL)
      isl_schedule_node_free(si->tmp_node);
  }
  SCOP_INFO.clear();
  STRINGS.clear();
  isl_ctx_free(ctx);
}

/******** node info *****************************************/

int
get_type(size_t scop_idx) {
  return isl_schedule_node_get_type(SCOP_INFO[scop_idx].current_node);
}

size_t
get_num_children(size_t scop_idx) {
  return isl_schedule_node_n_children(SCOP_INFO[scop_idx].current_node);
}

const char *
get_expr(size_t idx) {
  isl_schedule_node *node = SCOP_INFO[idx].current_node;
  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return "";
  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(node);
  const char *tmp = isl_multi_union_pw_aff_to_str(mupa);
  isl_multi_union_pw_aff_free(mupa);
  return tmp;
}

const char *
get_loop_signature(size_t scop_idx) {
  isl_schedule_node *node = SCOP_INFO[scop_idx].current_node;
  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return "[]";
  std::stringstream ss;
  isl_multi_union_pw_aff *mupa;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  assert(isl_multi_union_pw_aff_dim(mupa, isl_dim_out) == 1);
  // TODO save name
  isl_union_set *domain = isl_multi_union_pw_aff_domain(mupa);
  isl_size num_sets = isl_union_set_n_set(domain);
  isl_set_list *slist = isl_union_set_get_set_list(domain);
  ss << "[";
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    if (set_idx)
      ss << ", ";
    isl_set *set = isl_set_list_get_at(slist, set_idx);
    isl_size num_params = isl_set_dim(set, isl_dim_param);
    ss << "{'params' : [";
    for (isl_size di = 0; di < num_params; di++) {
      if (di)
        ss << ", ";
      ss << "'" << isl_set_get_dim_name(set, isl_dim_param, di) << "'";
    }
    ss << "], 'vars' :[";
    isl_size num_vars = isl_set_dim(set, isl_dim_set);
    for (isl_size di = 0; di < num_vars; di++) {
      if (di)
        ss << ", ";
      ss << "'" << isl_set_get_dim_name(set, isl_dim_set, di) << "'";
    }
    ss << "]}";
    isl_set_free(set);
  }
  ss << "]";
  isl_set_list_free(slist);
  isl_union_set_free(domain);
  STRINGS.push_back(ss.str());
  return STRINGS.back().c_str();
}

void
print_schedule_node(size_t scop_idx) {
  isl_schedule_node *node = SCOP_INFO[scop_idx].current_node;
  isl_schedule_node_dump(node);
}

/******** current node manipulation *************************/

void
reset_root(size_t scop_idx) {
  SCOP_INFO[scop_idx].current_node =
      isl_schedule_node_root(SCOP_INFO[scop_idx].current_node);
}

void
goto_parent(size_t scop_idx) {
  SCOP_INFO[scop_idx].current_node =
      isl_schedule_node_parent(SCOP_INFO[scop_idx].current_node);
}

void
goto_child(size_t scop_idx, size_t child_idx) {
  SCOP_INFO[scop_idx].current_node =
      isl_schedule_node_child(SCOP_INFO[scop_idx].current_node, child_idx);
}

/******** transformations ***********************************/

scop_info_t *
pre_transform(size_t scop_idx) {
  // Set up `tmp_node` as a copy of `current_node` because we don't
  // want to mess with the current node if the transformation is not
  // legal.
  //
  // However now that I think about it, this approach may be wrong,
  // since we might wanna get to illegal states, temporarily of course
  // - the only requirement is that we're in a legal state at the
  // final output.
  scop_info_t *si = &SCOP_INFO[scop_idx]; // Just save some typing.
  si->tmp_node = isl_schedule_node_copy(si->current_node);
  return si;
}

int
post_transform(size_t scop_idx) {
  scop_info_t *si = &SCOP_INFO[scop_idx]; // Just save some typing.
  isl_union_map *dep = isl_union_map_copy(si->dependency);
  isl_schedule_node *node = isl_schedule_node_copy(si->tmp_node);
  isl_schedule *sched = isl_schedule_node_get_schedule(node);
  node = isl_schedule_node_free(node);
  // Got `dep` and `sched`.
  isl_ctx *ctx = isl_schedule_get_ctx(sched);
  isl_bool legal = tadashi_check_legality(ctx, sched, si->dependency);
  isl_schedule_free(sched);
  si->modified = true;
  isl_schedule_node_free(si->current_node);
  si->current_node = si->tmp_node;
  si->tmp_node = NULL;
  return legal;
}

int
tile(size_t scop_idx, size_t tile_size) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_tile(si->tmp_node, tile_size);
  return post_transform(scop_idx);
}

int
interchange(size_t scop_idx) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_interchange(si->tmp_node);
  return post_transform(scop_idx);
}

int
fuse(size_t scop_idx, int idx1, int idx2) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_fuse(si->tmp_node, idx1, idx2);
  return post_transform(scop_idx);
}

int
full_fuse(size_t scop_idx) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_full_fuse(si->tmp_node);
  return post_transform(scop_idx);
}

int
partial_shift_var(size_t scop_idx, int pa_idx, long coeff, long var_idx) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node =
      tadashi_partial_shift_var(si->tmp_node, pa_idx, coeff, var_idx);
  return post_transform(scop_idx);
}

int
partial_shift_val(size_t scop_idx, int pa_idx, long val) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_partial_shift_val(si->tmp_node, pa_idx, val);
  return post_transform(scop_idx);
}

int
full_shift_var(size_t scop_idx, long coeff, long var_idx) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_full_shift_var(si->tmp_node, coeff, var_idx);
  return post_transform(scop_idx);
}

int
full_shift_val(size_t scop_idx, long val) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_full_shift_val(si->tmp_node, val);
  return post_transform(scop_idx);
}

int
full_shift_param(size_t scop_idx, long coeff, long param_idx) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node = tadashi_full_shift_param(si->tmp_node, coeff, param_idx);
  return post_transform(scop_idx);
}

int
partial_shift_param(size_t scop_idx, int pa_idx, long coeff, long param_idx) {
  scop_info_t *si = pre_transform(scop_idx);
  si->tmp_node =
      tadashi_partial_shift_param(si->tmp_node, pa_idx, coeff, param_idx);
  return post_transform(scop_idx);
}

void
set_loop_opt(size_t scop_idx, int pos, int opt) {
  isl_schedule_node *node = SCOP_INFO[scop_idx].current_node;
  node = isl_schedule_node_band_member_set_ast_loop_type(
      node, pos, (enum isl_ast_loop_type)opt);
  SCOP_INFO[scop_idx].current_node = node;
}

static __isl_give isl_printer *
generate_code_callback(__isl_take isl_printer *p, struct pet_scop *scop,
                       void *user) {
  isl_ctx *ctx;
  isl_schedule *sched;
  size_t *scop_idx = (size_t *)user;
  struct scop_info_t *scop_info = &SCOP_INFO[*scop_idx];

  if (!scop || !p)
    return isl_printer_free(p);
  if (!scop_info->modified) {
    p = pet_scop_print_original(scop, p);
  } else {
    sched = isl_schedule_node_get_schedule(scop_info->current_node);
    p = codegen(p, scop_info->scop, sched);
  }
  pet_scop_free(scop);
  (*scop_idx)++;
  return p;
}

int
generate_code(const char *input_path, const char *output_path) {
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

} // extern "C"
