/**
 * @file ctadashi.cc
 *
 * @brief ctadashi.cc is the entry point on the "C side" between the C and
 * Python code of tadashi.
 *
 * Loading a Python \p App object invokes \ref init_scops.
 */

#include <cstddef>
#include <sstream>

using namespace std;

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
#include <pet.h>

#include "ctadashi.h"

#include "codegen.h"
#include "legality.h"
#include "scops.h"
#include "transformations.h"

extern "C" Scops *
init_scops(char *input) {
  /**
   * Create a @ref Scop.
   */
  // pet_options_set_autodetect(ctx, 1);
  // pet_options_set_signed_overflow(ctx, 1);
  // pet_options_set_encapsulate_dynamic_control(ctx, 1);
  return new Scops(input);
}

extern "C" size_t
num_scops(Scops *app) {
  /**
   * Get the number of @ref Scop "Scop"s.
   */
  return app->scops.size();
}

extern "C" void
free_scops(Scops *app) {
  /**
   * Free the @ref Scops.
   */
  delete app;
}

/******** node info *****************************************/

extern "C" int
get_type(Scops *app, size_t scop_idx) {
  return isl_schedule_node_get_type(app->scops[scop_idx]->current_node);
}

extern "C" size_t
get_num_children(Scops *app, size_t scop_idx) {
  return isl_schedule_node_n_children(app->scops[scop_idx]->current_node);
}

extern "C" const char *
get_expr(Scops *app, size_t scop_idx) {
  Scop *si = app->scops[scop_idx];
  if (isl_schedule_node_get_type(si->current_node) != isl_schedule_node_band)
    return "";
  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(si->current_node);
  char *tmp = isl_multi_union_pw_aff_to_str(mupa);
  mupa = isl_multi_union_pw_aff_free(mupa);
  return si->add_string(tmp);
}

extern "C" const char *
get_label(Scops *app, size_t scop_idx) {
  Scop *si = app->scops[scop_idx];
  isl_multi_union_pw_aff *mupa;
  if (isl_schedule_node_get_type(si->current_node) != isl_schedule_node_band)
    return "foo";
  mupa = isl_schedule_node_band_get_partial_schedule(si->current_node);
  const char *label = isl_multi_union_pw_aff_get_tuple_name(mupa, isl_dim_out);
  mupa = isl_multi_union_pw_aff_free(mupa);
  std::stringstream ss;
  ss << label;
  return si->add_string(ss);
}

extern "C" const char *
get_loop_signature(Scops *app, size_t scop_idx) {
  Scop *si = app->scops[scop_idx];
  if (isl_schedule_node_get_type(si->current_node) != isl_schedule_node_band)
    return "[]";
  std::stringstream ss;
  isl_multi_union_pw_aff *mupa;
  mupa = isl_schedule_node_band_get_partial_schedule(si->current_node);
  // assert(isl_multi_union_pw_aff_dim(mupa, isl_dim_out) == 1);
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
print_schedule_node(Scops *app, size_t scop_idx) {
  isl_schedule_node *node = app->scops[scop_idx]->current_node;
  return isl_schedule_node_to_str(node);
}

/******** current node manipulation *************************/

extern "C" void
goto_root(Scops *app, size_t scop_idx) {
  app->scops[scop_idx]->current_node =
      isl_schedule_node_root(app->scops[scop_idx]->current_node);
}

extern "C" void
goto_parent(Scops *app, size_t scop_idx) {
  app->scops[scop_idx]->current_node =
      isl_schedule_node_parent(app->scops[scop_idx]->current_node);
}

extern "C" void
goto_child(Scops *app, size_t scop_idx, size_t child_idx) {
  app->scops[scop_idx]->current_node =
      isl_schedule_node_child(app->scops[scop_idx]->current_node, child_idx);
}

extern "C" void
rollback(Scops *app, size_t scop_idx) {
  app->scops[scop_idx]->rollback();
}

void
reset_scop(Scops *app, size_t scop_idx) {
  app->scops[scop_idx]->reset();
}

static __isl_give isl_printer *
generate_code_callback(__isl_take isl_printer *p, struct pet_scop *scop,
                       void *user) {
  isl_ctx *ctx;
  isl_schedule *sched;
  Scop **si_ptr = (Scop **)user;
  Scop *si = *si_ptr;
  if (!scop || !p)
    return isl_printer_free(p);
  if (!si->modified) {
    p = pet_scop_print_original(scop, p);
  } else {
    sched = isl_schedule_node_get_schedule(si->current_node);
    p = codegen(p, si->scop->pet_scop, sched);
  }
  pet_scop_free(scop);
  si_ptr++;
  return p;
}

extern "C" int
generate_code(Scops *app, const char *input_path, const char *output_path) {
  int r = 0;
  isl_ctx *ctx = app->ctx;
  size_t scop_idx = 0;

  //   isl_options_set_ast_print_macro_once(ctx, 1);
  //   pet_options_set_encapsulate_dynamic_control(ctx, 1);

  FILE *output_file = fopen(output_path, "w");
  Scop **si = app->scops.data();
  r = pet_transform_C_source(ctx, input_path, output_file,
                             generate_code_callback, si);
  fclose(output_file);
  return r;
}

/******** transformations ***********************************/

/**
 * @section Transformations
 *
 * All transformations take a \p app, and \p scop_idx, and return 0,
 * 1, -1.
 *
 * Which SCoP is transformed is determined by \p app which selects the
 * @ref Scops corresponding to the Python \p App instance,
 * and \p scop_idx determine the which @ref Scop within the app.
 *
 * Return values are:
 * - 1 for legal
 * - 0 for illegal
 * - -1 for "same as previous"
 */

extern "C" int
tile1d(Scops *app, size_t scop_idx, size_t tile_size) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_tile_1d, tile_size);
}

extern "C" int
tile2d(Scops *app, size_t scop_idx, size_t size1, size_t size2) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_tile_2d, size1, size2);
}

extern "C" int
tile3d(Scops *app, size_t scop_idx, size_t size1, size_t size2, size_t size3) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_tile_3d, size1, size2, size3);
}

extern "C" int
interchange(Scops *app, size_t scop_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_interchange);
}

extern "C" int
fuse(Scops *app, size_t scop_idx, int idx1, int idx2) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_fuse, idx1, idx2);
}

extern "C" int
full_fuse(Scops *app, size_t scop_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_full_fuse);
}

int
split(Scops *app, size_t scop_idx, int split) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_split, split);
}

int
full_split(Scops *app, size_t scop_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_full_split);
}

extern "C" int
partial_shift_var(Scops *app, size_t scop_idx, int pa_idx, long coeff,
                  long var_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_partial_shift_var, pa_idx,
                                             coeff, var_idx);
}

extern "C" int
partial_shift_val(Scops *app, size_t scop_idx, int pa_idx, long val) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_partial_shift_val, pa_idx, val);
}

extern "C" int
partial_shift_param(Scops *app, size_t scop_idx, int pa_idx, long coeff,
                    long param_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_partial_shift_param,
                                             pa_idx, coeff, param_idx);
}

extern "C" int
full_shift_var(Scops *app, size_t scop_idx, long coeff, long var_idx) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_full_shift_var, coeff, var_idx);
}

extern "C" int
full_shift_val(Scops *app, size_t scop_idx, long val) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_full_shift_val, val);
}

extern "C" int
full_shift_param(Scops *app, size_t scop_idx, long coeff, long param_idx) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_full_shift_param, coeff, param_idx);
}

extern "C" int
set_parallel(Scops *app, size_t scop_idx, int num_threads) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality_parallel,
                                             tadashi_set_parallel, num_threads);
}

extern "C" int
set_loop_opt(Scops *app, size_t scop_idx, int pos, int opt) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, isl_schedule_node_band_member_set_ast_loop_type,
      pos, (enum isl_ast_loop_type)opt);
}
