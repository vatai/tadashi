#include <assert.h>
#include <iostream>
#include <isl/schedule.h>
#include <isl/schedule_node.h>

#include "ccscop.h"

ccScop::~ccScop() {
#ifndef NDEBUG
  std::cout << "<<< [d]Default()";
  dealloc();
  std::cout << std::endl;
#endif // NDEBUG
}

ccScop::ccScop() : current_node(nullptr), scop(nullptr) {
#ifndef NDEBUG
  std::cout << ">>> [c]Default()" << std::endl;
#endif // NDEBUG
}

ccScop::ccScop(pet_scop *ps) : scop(ps) {
#ifndef NDEBUG
  std::cout << ">>> [c]PetPtr()" << std::endl;
#endif // NDEBUG
  isl_schedule *sched = pet_scop_get_schedule(ps);
  this->current_node = isl_schedule_get_root(sched);
  isl_schedule_free(sched);
}

void
ccScop::dealloc() {
  if (this->current_node != nullptr)
    this->current_node = isl_schedule_node_free(this->current_node);
  if (this->scop != nullptr)
    this->scop = pet_scop_free(this->scop);
}
