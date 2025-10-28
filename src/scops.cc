#include <cstdio>
#include <deque>
#include <sstream>
#include <vector>

#include <isl/union_map.h>
#include <pet.h>

#include "legality.h"
#include "scops.h"

Scop::Scop(pet_scop *ps) : tmp_node(nullptr), modified(false) {
  scop = allocate_tadashi_scop(ps);
  current_node = isl_schedule_get_root(scop->schedule);
}

Scop::~Scop() {
  isl_schedule_node_free(current_node);
  if (tmp_node != nullptr)
    isl_schedule_node_free(tmp_node);
  free_tadashi_scop(scop);
  // printf("<<< ~Scop()\n");
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

// Scops

__isl_give isl_printer *
get_scop_callback(__isl_take isl_printer *p, pet_scop *scop, void *user) {
  std::vector<Scop *> *scops = (std::vector<Scop *> *)user;
  scops->push_back(new Scop(scop));
  return p;
}

Scops::Scops(char *input) : ctx(isl_ctx_alloc_with_pet_options()) {

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
