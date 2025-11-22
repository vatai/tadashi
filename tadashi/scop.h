#ifndef SCOP_H
#define SCOP_H

#include <string>

#include <pet.h>

class Scop {
public:
  pet_scop *scop;
  Scop(pet_scop *scop);
  virtual ~Scop();
  std::string to_string();
};

#endif
