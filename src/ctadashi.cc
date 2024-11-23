/** @file */
// Date: 2024, January
// Author: Emil VATAI, Riken
//
// This file is the "C side" between the C and Python code of tadashi.

#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <isl/aff_type.h>
#include <isl/space_type.h>
#include <pet.h>
#include <sstream>

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

#include "ctadashi.h"

#include "codegen.h"
#include "legality.h"
#include "scops.h"
#include "transformations.h"

ScopsPool SCOPS_POOL;

/// Entry point.
extern "C" size_t
init_scops(char *input) { // Entry point
  // pet_options_set_autodetect(ctx, 1);
  // pet_options_set_signed_overflow(ctx, 1);
  // pet_options_set_encapsulate_dynamic_control(ctx, 1);
  size_t pool_idx = SCOPS_POOL.add(input);
  return pool_idx;
}

extern "C" size_t
num_scops(size_t pool_idx) {
  return SCOPS_POOL[pool_idx].scops.size();
}

extern "C" void
free_scops(size_t pool_idx) {
  SCOPS_POOL.remove(pool_idx);
}

/******** node info *****************************************/

extern "C" int
get_type(size_t pool_idx, size_t scop_idx) {
  return isl_schedule_node_get_type(
      SCOPS_POOL[pool_idx].scops[scop_idx].current_node);
}

extern "C" size_t
get_num_children(size_t pool_idx, size_t scop_idx) {
  return isl_schedule_node_n_children(
      SCOPS_POOL[pool_idx].scops[scop_idx].current_node);
}

extern "C" const char *
get_expr(size_t pool_idx, size_t idx) {
  Scop *si = &SCOPS_POOL[pool_idx].scops[idx];
  if (isl_schedule_node_get_type(si->current_node) != isl_schedule_node_band)
    return "";
  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(si->current_node);
  char *tmp = isl_multi_union_pw_aff_to_str(mupa);
  mupa = isl_multi_union_pw_aff_free(mupa);
  return si->add_string(tmp);
}

extern "C" const char *
get_loop_signature(size_t pool_idx, size_t scop_idx) {
  Scop *si = &SCOPS_POOL[pool_idx].scops[scop_idx];
  if (isl_schedule_node_get_type(si->current_node) != isl_schedule_node_band)
    return "[]";
  std::stringstream ss;
  isl_multi_union_pw_aff *mupa;
  mupa = isl_schedule_node_band_get_partial_schedule(si->current_node);
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
  return si->add_string(ss);
}

extern "C" const char *
print_schedule_node(size_t pool_idx, size_t scop_idx) {
  isl_schedule_node *node = SCOPS_POOL[pool_idx].scops[scop_idx].current_node;
  return isl_schedule_node_to_str(node);
}

/******** current node manipulation *************************/

extern "C" void
goto_root(size_t pool_idx, size_t scop_idx) {
  SCOPS_POOL[pool_idx].scops[scop_idx].current_node =
      isl_schedule_node_root(SCOPS_POOL[pool_idx].scops[scop_idx].current_node);
}

extern "C" void
goto_parent(size_t pool_idx, size_t scop_idx) {
  SCOPS_POOL[pool_idx].scops[scop_idx].current_node = isl_schedule_node_parent(
      SCOPS_POOL[pool_idx].scops[scop_idx].current_node);
}

extern "C" void
goto_child(size_t pool_idx, size_t scop_idx, size_t child_idx) {
  SCOPS_POOL[pool_idx].scops[scop_idx].current_node = isl_schedule_node_child(
      SCOPS_POOL[pool_idx].scops[scop_idx].current_node, child_idx);
}

extern "C" void
rollback(size_t pool_idx, size_t scop_idx) {
  Scop *si = &SCOPS_POOL[pool_idx].scops[scop_idx];
  isl_schedule_node *tmp = si->tmp_node;
  si->tmp_node = si->current_node;
  si->current_node = tmp;
}

static __isl_give isl_printer *
generate_code_callback(__isl_take isl_printer *p, struct pet_scop *scop,
                       void *user) {
  isl_ctx *ctx;
  isl_schedule *sched;
  size_t *scop_idx = (size_t *)user;
  struct Scop *scop_info = &SCOPS_POOL[0].scops[*scop_idx];

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

extern "C" int
generate_code(size_t pool_idx, const char *input_path,
              const char *output_path) {
  int r = 0;
  isl_ctx *ctx = SCOPS_POOL[pool_idx].ctx;
  size_t scop_idx = 0;

  //   isl_options_set_ast_print_macro_once(ctx, 1);
  //   pet_options_set_encapsulate_dynamic_control(ctx, 1);

  FILE *output_file = fopen(output_path, "w");
  r = pet_transform_C_source(ctx, input_path, output_file,
                             generate_code_callback, &scop_idx);
  fclose(output_file);
  return r;
}

/******** transformations ***********************************/

extern "C" Scop *
pre_transform(size_t pool_idx, size_t scop_idx) {
  // Set up `tmp_node` as a copy of `current_node` because we don't
  // want to mess with the current node if the transformation is not
  // legal.
  //
  // However now that I think about it, this approach may be wrong,
  // since we might wanna get to illegal states, temporarily of course
  // - the only requirement is that we're in a legal state at the
  // final output.
  Scop *si = &SCOPS_POOL[pool_idx].scops[scop_idx]; // Just save some typing.
  if (si->tmp_node != NULL)
    si->tmp_node = isl_schedule_node_free(si->tmp_node);
  si->tmp_node = isl_schedule_node_copy(si->current_node);
  return si;
}

extern "C" int
post_transform(size_t pool_idx, size_t scop_idx) {
  Scop *si = &SCOPS_POOL[pool_idx].scops[scop_idx]; // Just save some typing.
  isl_union_map *dep = isl_union_map_copy(si->dependency);
  isl_schedule *sched = isl_schedule_node_get_schedule(si->tmp_node);
  // Got `dep` and `sched`.
  isl_ctx *ctx = isl_schedule_get_ctx(sched);
  isl_bool legal = tadashi_check_legality(ctx, sched, si->dependency);
  isl_schedule_free(sched);
  si->modified = true;
  isl_schedule_node *node = si->current_node;
  si->current_node = si->tmp_node;
  si->tmp_node = node;
  return legal;
}

extern "C" int
tile(size_t pool_idx, size_t scop_idx, size_t tile_size) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_tile(si->tmp_node, tile_size);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
interchange(size_t pool_idx, size_t scop_idx) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_interchange(si->tmp_node);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
fuse(size_t pool_idx, size_t scop_idx, int idx1, int idx2) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_fuse(si->tmp_node, idx1, idx2);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
full_fuse(size_t pool_idx, size_t scop_idx) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_full_fuse(si->tmp_node);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
partial_shift_var(size_t pool_idx, size_t scop_idx, int pa_idx, long coeff,
                  long var_idx) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node =
      tadashi_partial_shift_var(si->tmp_node, pa_idx, coeff, var_idx);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
partial_shift_val(size_t pool_idx, size_t scop_idx, int pa_idx, long val) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_partial_shift_val(si->tmp_node, pa_idx, val);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
full_shift_var(size_t pool_idx, size_t scop_idx, long coeff, long var_idx) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_full_shift_var(si->tmp_node, coeff, var_idx);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
full_shift_val(size_t pool_idx, size_t scop_idx, long val) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_full_shift_val(si->tmp_node, val);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
full_shift_param(size_t pool_idx, size_t scop_idx, long coeff, long param_idx) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_full_shift_param(si->tmp_node, coeff, param_idx);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
partial_shift_param(size_t pool_idx, size_t scop_idx, int pa_idx, long coeff,
                    long param_idx) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node =
      tadashi_partial_shift_param(si->tmp_node, pa_idx, coeff, param_idx);
  return post_transform(pool_idx, scop_idx);
}

extern "C" int
set_parallel(size_t pool_idx, size_t scop_idx) {
  Scop *si = pre_transform(pool_idx, scop_idx);
  si->tmp_node = tadashi_set_parallel(si->tmp_node);
  isl_union_map *dep = isl_union_map_copy(si->dependency);
  isl_schedule_node *node = isl_schedule_node_copy(si->tmp_node);
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  node = isl_schedule_node_first_child(node);
  isl_bool legal = tadashi_check_legality_parallel(ctx, node, si->dependency);
  node = isl_schedule_node_free(node);
  si->modified = true;
  node = si->current_node;
  si->current_node = si->tmp_node;
  si->tmp_node = node;
  return legal;
}

extern "C" int
set_loop_opt(size_t pool_idx, size_t scop_idx, int pos, int opt) {
  isl_schedule_node *node = SCOPS_POOL[pool_idx].scops[scop_idx].current_node;
  node = isl_schedule_node_band_member_set_ast_loop_type(
      node, pos, (enum isl_ast_loop_type)opt);
  SCOPS_POOL[0].scops[scop_idx].current_node = node;
  return 1;
}
