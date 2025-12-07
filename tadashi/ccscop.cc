#include "ccscop.h"
#include <iostream>

#include "ccscop.h"

ccScop::~ccScop() {
  std::cout << "<<< [d]Default" << std::endl;
  pet_scop_free(this->scop);
}
ccScop::ccScop() : scop(nullptr) {
  std::cout << ">>> [c]Default" << std::endl; //
}
ccScop::ccScop(pet_scop *ps) : scop(ps) {
  std::cout << ">>> [c]PetPtr" << std::endl;
}
