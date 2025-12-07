#ifndef TADASHI_SCOP_H
#define TADASHI_SCOP_H

#include <pet.h>

class TadashiScop {
public:
  TadashiScop();
  TadashiScop(pet_scop *ps);

  // private:
  pet_scop *scop;
};

#endif
