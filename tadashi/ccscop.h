#ifndef TADASHI_SCOP_H
#define TADASHI_SCOP_H

#include <pet.h>

class ccScop {
public:
  virtual ~ccScop();
  ccScop();
  ccScop(pet_scop *ps);
  void dealloc();

public:
  isl_schedule_node *current_node;

private:
  pet_scop *scop;
};

#endif
