#include <deque>
#include <sstream>
#include <vector>

#include <pet.h>

#include "legality.h"
#include "scops.h"

Scop::Scop(pet_scop *scop) : scop(scop), tmp_node(nullptr), modified(false) {
  dependency = get_dependencies(scop);
  isl_schedule *schedule = pet_scop_get_schedule(scop);
  current_node = isl_schedule_get_root(schedule);
  schedule = isl_schedule_free(schedule);
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

__isl_give isl_printer *
get_scop_callback(__isl_take isl_printer *p, pet_scop *scop, void *user) {
  std::vector<Scop> *scops = (std::vector<Scop> *)user;
  scops->emplace_back(scop);
  return p;
}

Scops::Scops(char *input) : ctx(isl_ctx_alloc_with_pet_options()) {
  FILE *output = fopen("/dev/null", "w");
  // pet_options_set_autodetect(ctx, 1);
  // pet_options_set_signed_overflow(ctx, 1);
  // pet_options_set_encapsulate_dynamic_control(ctx, 1);
  pet_transform_C_source(ctx, input, output, get_scop_callback, &scops);
  fclose(output);
};

int
Scops::num_scops() {
  return scops.size();
}

Scops::~Scops() {
  // if (SCOPS_POOL[pool_idx].scops.size() == 0)
  //   return;
  for (size_t i = 0; i < scops.size(); ++i) {
    Scop *si = &scops[i];
    isl_union_map_free(si->dependency);
    isl_schedule_node_free(si->current_node);
    if (si->tmp_node != nullptr)
      isl_schedule_node_free(si->tmp_node);
    pet_scop_free(si->scop);
    // si->strings.clear();
  }
  scops.clear();
  isl_ctx_free(ctx);
};

size_t
ScopsPool::add(char *input) {
  size_t index = 0;
  Scops *scops_ptr = new Scops(input);
  if (!free_indexes.empty()) {
    index = free_indexes.front();
    scops_map[index] = scops_ptr;
  } else {
    scops_map.push_back(scops_ptr);
  }
  return index;
}

void
ScopsPool::remove(size_t pool_idx) {
  delete scops_map[pool_idx];
  scops_map[pool_idx] = nullptr;
  free_indexes.push_back(pool_idx);
};

Scops &
ScopsPool::operator[](size_t idx) {
  return *scops_map[idx];
}
