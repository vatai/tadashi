#include <algorithm>
#include <cstdio>
#include <deque>
#include <sstream>
#include <string>
#include <vector>

#include <isl/union_map.h>
#include <pet.h>

#include "legality.h"
#include "scops.h"

Scop::Scop(pet_scop *ps)
    : tmp_node(nullptr), modified(false), current_legal(true) {
  scop = allocate_tadashi_scop(ps);
  current_node = isl_schedule_get_root(scop->schedule);
}

Scop::~Scop() {
  isl_schedule_node_free(current_node);
  if (tmp_node != nullptr)
    isl_schedule_node_free(tmp_node);
  free_tadashi_scop(scop);
}

const char *
Scop::add_string(char *str) {
  strings.push_back(str);
  free(str);
  return strings.back().c_str();
};

const char *
Scop::add_string(std::stringstream &ss) {
  strings.push_back(ss.str());
  return strings.back().c_str();
}

void
Scop::rollback() {
  if (!modified)
    return;
  std::swap(current_legal, tmp_legal);
  std::swap(current_node, tmp_node);
}

void
Scop::reset() {
  if (!modified)
    return;
  current_node = isl_schedule_node_free(current_node);
  current_node = isl_schedule_get_root(scop->schedule);
  current_legal = true;
  tmp_node = isl_schedule_node_free(tmp_node);
  tmp_node = nullptr;
  tmp_legal = false;
  modified = false;
}

// Scops

__isl_give isl_printer *
get_scop_callback(__isl_take isl_printer *p, pet_scop *scop, void *user) {
  std::vector<Scop *> *scops = (std::vector<Scop *> *)user;
  scops->push_back(new Scop(scop));
  return p;
}

Scops::Scops(char *input, const std::vector<std::string> &defines)
    : ctx(isl_ctx_alloc_with_pet_options()) {
  for (const auto &s : defines)
    pet_options_append_defines(ctx, s.c_str());
  // printf("Scops::Scops(ctx=%p)\n", ctx);
  FILE *output = fopen("/dev/null", "w");
  // pet_options_set_autodetect(ctx, 1);
  // pet_options_set_signed_overflow(ctx, 1);
  // pet_options_set_encapsulate_dynamic_control(ctx, 1);
  pet_transform_C_source(ctx, input, output, get_scop_callback, &scops);
  fclose(output);
  // printf("Scops::Scops(ctx=%p)\n", ctx);
};

Scops::~Scops() {
  for (Scop *p : scops)
    delete p;
  scops.clear();
  // printf("Scops::~Scops(ctx=%p)\n", ctx);
  isl_ctx_free(ctx);
};

int
Scops::num_scops() {
  return scops.size();
}
