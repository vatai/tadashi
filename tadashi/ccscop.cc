#include "ccscop.h"
#include <iostream>

#include "ccscop.h"

ccScop::~ccScop() {
  // std::cout << "<<< [d]Default(" << id << ")";
  dealloc();
  // std::cout << std::endl;
}

ccScop::ccScop() : scop(nullptr) {
  // std::cout << ">>> [c]Default(" << id << ")" << std::endl;
}

ccScop::ccScop(pet_scop *ps) : scop(ps) {
  // std::cout << ">>> [c]PetPtr(" << id << ")" << std::endl;
}

void
ccScop::dealloc() {
  if (this->scop != nullptr) {
    pet_scop_free(this->scop);
    this->scop = nullptr;
  }
}
