/**
 * @file ctadashi.cc
 *
 * @brief ctadashi.cc is the entry point on the "C side" between the C and
 * Python code of tadashi.
 *
 * Loading a Python \p App object invokes \ref init_scops.
 */

#include <cassert>
#include <climits>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <isl/union_map_type.h>
#include <sstream>
#include <string>
#include <vector>

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

Scops *
init_scops(char *input, const std::vector<std::string> &defines) {
  /**
   * Create a @ref Scop.
   */
  return new Scops(input, defines);
}

PollyApp *
init_scops_from_json(char *compiler, char *input) {
  return new PollyApp(compiler, input);
}

size_t
num_scops(Scops *app) {
  /**
   * Get the number of @ref Scop "Scop"s.
   */
  return app->scops.size();
}

void
free_scops(Scops *app) {
  /**
   * Free the @ref Scops.
   */
  delete app;
}

/******** node info *****************************************/

const char *
print_schedule_node(Scops *app, size_t scop_idx) {
  isl_schedule_node *node = app->scops[scop_idx]->current_node;
  return isl_schedule_node_to_str(node);
}

/******** current node manipulation *************************/

int
get_legal(Scops *app, size_t scop_idx) {
  return app->scops[scop_idx]->current_legal;
}

void
rollback(Scops *app, size_t scop_idx) {
  app->scops[scop_idx]->rollback();
}

void
reset_scop(Scops *app, size_t scop_idx) {
  app->scops[scop_idx]->reset();
}

int
generate_code(Scops *app, const char *input_path, const char *output_path) {
  PollyApp *polly_app = dynamic_cast<PollyApp *>(app);
  if (polly_app)
    return polly_app->generate_code(input_path, output_path);
  if (app->scops.size() == 0)
    return 0;
  return generate_code_isl(app, input_path, output_path);
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

int
tile1d(Scops *app, size_t scop_idx, size_t tile_size) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_tile_1d, tile_size);
}

int
tile2d(Scops *app, size_t scop_idx, size_t size1, size_t size2) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_tile_2d, size1, size2);
}

int
tile3d(Scops *app, size_t scop_idx, size_t size1, size_t size2, size_t size3) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_tile_3d, size1, size2, size3);
}

int
interchange(Scops *app, size_t scop_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_interchange);
}

int
fuse(Scops *app, size_t scop_idx, int idx1, int idx2) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_fuse, idx1, idx2);
}

int
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

int
partial_shift_var(Scops *app, size_t scop_idx, int pa_idx, long coeff,
                  long var_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_partial_shift_var, pa_idx,
                                             coeff, var_idx);
}

int
partial_shift_val(Scops *app, size_t scop_idx, int pa_idx, long val) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_partial_shift_val, pa_idx, val);
}

int
partial_shift_param(Scops *app, size_t scop_idx, int pa_idx, long coeff,
                    long param_idx) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_partial_shift_param,
                                             pa_idx, coeff, param_idx);
}

int
full_shift_var(Scops *app, size_t scop_idx, long coeff, long var_idx) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_full_shift_var, coeff, var_idx);
}

int
full_shift_val(Scops *app, size_t scop_idx, long val) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality,
                                             tadashi_full_shift_val, val);
}

int
full_shift_param(Scops *app, size_t scop_idx, long coeff, long param_idx) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, tadashi_full_shift_param, coeff, param_idx);
}

int
set_parallel(Scops *app, size_t scop_idx, int num_threads) {
  return app->scops[scop_idx]->run_transform(tadashi_check_legality_parallel,
                                             tadashi_set_parallel, num_threads);
}

int
set_loop_opt(Scops *app, size_t scop_idx, int pos, int opt) {
  return app->scops[scop_idx]->run_transform(
      tadashi_check_legality, isl_schedule_node_band_member_set_ast_loop_type,
      pos, (enum isl_ast_loop_type)opt);
}
