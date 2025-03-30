#include <cstdio>
#include <deque>
#include <sstream>
#include <vector>

#include <isl/union_map.h>
#include <pet.h>

#include "legality.h"
#include "scops.h"

Scop::Scop(pet_scop *ps) : tmp_node(nullptr), modified(false) {
  populate_tadashi_scop(&scop, ps);
  current_node = isl_schedule_get_root(scop.schedule);
}

Scop::~Scop() {
  isl_schedule_node_free(current_node);
  free_tadashi_scop(&scop);
  if (tmp_node != nullptr)
    isl_schedule_node_free(tmp_node);
  pet_scop_free(this->scop.pet_scop);
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
  std::vector<Scop> *scops = (std::vector<Scop> *)user;
  scops->emplace_back(scop);
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
  scops.clear();
  // printf("Scops::~Scops(ctx=%p)\n", ctx);
  isl_ctx_free(ctx);
};

int
Scops::num_scops() {
  return scops.size();
}

// POOL

// ScopsPool::ScopsPool() {
//   // printf("> ScopsPool()\n"); //
// }

ScopsPool::~ScopsPool() {
  size_t size = scops_vector.size();
  for (int pool_idx = 0; pool_idx < size; pool_idx++) {
    if (scops_vector[pool_idx] != nullptr)
      delete scops_vector[pool_idx];
  }
  // scops_map.clear();
  // free_indexes.clear();
  // printf("< ~ScopsPool()\n");
}

size_t
ScopsPool::add(char *input) {
  size_t index = scops_vector.size();
  Scops *scops_ptr = new Scops(input);
  if (!free_indexes.empty()) {
    index = free_indexes.front();
    free_indexes.pop_front();
    scops_vector[index] = scops_ptr;
  } else {
    scops_vector.push_back(scops_ptr);
  }
  return index;
}

void
ScopsPool::remove(size_t pool_idx) {
  delete scops_vector[pool_idx];
  scops_vector[pool_idx] = nullptr;
  free_indexes.push_back(pool_idx);
};

Scops &
ScopsPool::operator[](size_t idx) {
  return *scops_vector[idx];
}
