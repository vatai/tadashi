#include <iostream>

#include "tadashi_scop.h"

TadashiScop::TadashiScop() : scop(nullptr) {
  std::cout << "Spam Spam!" << std::endl;
}
TadashiScop::TadashiScop(pet_scop *ps) : scop(ps) {
  std::cout << "Foo bar!" << std::endl;
}
