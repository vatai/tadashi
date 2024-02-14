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

#include <legality.h>

extern "C" {

struct scop_admin_t {
  pet_scop *scop;
  isl_union_map *dependency;
  isl_schedule_node *current_node;
  bool modified;
};

std::vector<struct scop_admin_t> SCOP_ADMIN;

__isl_give isl_printer *get_scop(__isl_take isl_printer *p, pet_scop *scop,
                                 void *user) {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(sched);
  isl_schedule_free(sched);
  SCOP_ADMIN.push_back({scop, get_dependencies(scop), node, false});
  return p;
}

int get_num_scops(char *input) { // Entry point

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");
  // pet_options_set_autodetect(ctx, 1);
  SCOP_ADMIN.clear();
  pet_transform_C_source(ctx, input, output, get_scop, NULL);
  fclose(output);
  return SCOP_ADMIN.size();
}

void free_scops() {
  if (SCOP_ADMIN.size() == 0)
    return;
  isl_set *set = pet_scop_get_context(SCOP_ADMIN[0].scop);
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_set_free(set);
  for (size_t i = 0; i < SCOP_ADMIN.size(); ++i) {
    isl_union_map_free(SCOP_ADMIN[i].dependency);
    pet_scop_free(SCOP_ADMIN[i].scop);
    isl_schedule_node_free(SCOP_ADMIN[i].current_node);
  }
  SCOP_ADMIN.clear();
  isl_ctx_free(ctx);
}

int get_type(size_t scop_idx) {
  return isl_schedule_node_get_type(SCOP_ADMIN[scop_idx].current_node);
}

const char *get_type_str(size_t scop_idx) {
  enum isl_schedule_node_type type;
  type = isl_schedule_node_get_type(SCOP_ADMIN[scop_idx].current_node);
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
  return isl_schedule_node_n_children(SCOP_ADMIN[scop_idx].current_node);
}

void goto_parent(size_t scop_idx) {
  SCOP_ADMIN[scop_idx].current_node =
      isl_schedule_node_parent(SCOP_ADMIN[scop_idx].current_node);
}

void goto_child(size_t scop_idx, size_t child_idx) {
  SCOP_ADMIN[scop_idx].current_node =
      isl_schedule_node_child(SCOP_ADMIN[scop_idx].current_node, child_idx);
}

const char *get_expr(size_t idx) {
  isl_schedule_node *node = SCOP_ADMIN[idx].current_node;
  if (isl_schedule_node_get_type(node) != isl_schedule_node_band)
    return "";
  isl_multi_union_pw_aff *mupa =
      isl_schedule_node_band_get_partial_schedule(node);
  const char *tmp = isl_multi_union_pw_aff_to_str(mupa);
  isl_multi_union_pw_aff_free(mupa);
  return tmp;
}

const char *get_dim_names(size_t scop_idx) {
  isl_schedule_node *node = SCOP_ADMIN[scop_idx].current_node;
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
  isl_schedule *sched = pet_scop_get_schedule(SCOP_ADMIN[scop_idx].scop);
  const char *ptr = isl_schedule_to_str(sched);
  isl_schedule_free(sched);
  return ptr;
}

void reset_root(size_t scop_idx) {
  SCOP_ADMIN[scop_idx].current_node =
      isl_schedule_node_root(SCOP_ADMIN[scop_idx].current_node);
}

void tile(size_t scop_idx, size_t tile_size) {
  SCOP_ADMIN[scop_idx].modified = true;
  isl_schedule_node *&node = SCOP_ADMIN[scop_idx].current_node;
  isl_ctx *ctx = isl_schedule_node_get_ctx(node);
  node = isl_schedule_node_band_tile(
      node, isl_multi_val_from_val_list(
                isl_schedule_node_band_get_space(node),
                isl_val_list_from_val(isl_val_int_from_si(ctx, tile_size))));
}

struct generate_code_user_t {
  size_t scop_idx;
  isl_union_map *deps;
  isl_schedule_node *node;
};

// __isl_give isl_printer *transform_scop(isl_ctx *ctx, __isl_take isl_printer
// *p,
//                                        __isl_keep struct pet_scop *scop,
//                                        struct user_t *user) {
//   isl_schedule *schedule;
//   isl_union_map *dependencies;
//   isl_printer *tmp;
//   dependencies = get_dependencies(scop);
//   printf("\nPrinting dependencies...\n");
//   tmp = new_printer(ctx, user->opt->source_file_path, user->scop_counter,
//                     user->opt->dependencies_suffix);
//   tmp = isl_printer_print_union_map(tmp, dependencies);
//   delete_printer(tmp);

//   schedule = get_schedule(ctx, scop, user);
//   if (user->opt->legality_check) {
//     if (!check_schedule_legality(ctx, schedule, dependencies)) {
//       printf("Illegal schedule!\n");
//       isl_schedule_free(schedule);
//       schedule = pet_scop_get_schedule(scop);
//     } else
//       printf("Schedule is legal!\n");
//   } else {
//     printf("Schedule not checked!\n");
//     isl_union_map_free(dependencies);
//   }
//   p = generate_code(ctx, p, scop, schedule);
//   return p;
// }

static __isl_give isl_printer *foreach_scop_callback(__isl_take isl_printer *p,
                                                     struct pet_scop *scop,
                                                     void *_user) {
  //   isl_ctx *ctx;
  //   struct user_t *user = _user;
  //   isl_printer *tmp;

  //   printf("Begin processing SCOP %lu\n", user->scop_counter);
  //   if (!scop || !p)
  //     return isl_printer_free(p);
  //   ctx = isl_printer_get_ctx(p);

  //   print_schedule(ctx, scop->schedule, user->scop_counter);

  //   tmp = new_printer(ctx, user->opt->source_file_path, user->scop_counter,
  //                     user->opt->original_schedule_suffix);
  //   tmp = isl_printer_print_schedule(tmp, scop->schedule);
  //   delete_printer(tmp);
  //   p = transform_scop(ctx, p, scop, user);
  //   pet_scop_free(scop);
  //   printf("End processing SCOP %lu\n", user->scop_counter);
  //   user->scop_counter++;
  return p;
}

int generate_code(const char *input_path, const char *output_path) {
  int r;
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();

  //   isl_options_set_ast_print_macro_once(ctx, 1);
  //   pet_options_set_encapsulate_dynamic_control(ctx, 1);

  FILE *output_file = fopen(output_path, "w");
  r = pet_transform_C_source(ctx, input_path, output_file,
                             foreach_scop_callback, NULL);
  //   fprintf(stderr, "Number of scops: %lu\n", user.scop_counter);
  //   fclose(output_file);
  //   isl_ctx_free(ctx);
  //   printf("### STOP ###\n");
  return r;
}

// not needed? //

size_t depth(size_t scop_idx) {
  return isl_schedule_node_get_tree_depth(SCOP_ADMIN[scop_idx].current_node);
}

size_t child_position(size_t scop_idx) {
  return isl_schedule_node_get_child_position(
      SCOP_ADMIN[scop_idx].current_node);
}

} // extern "C"
