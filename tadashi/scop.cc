#include "scop.h"

#include <iostream>
#include <string>

#include <isl/schedule.h>

Scop::Scop(pet_scop *scop) : scop(scop) {}
Scop::~Scop() {
  if (scop)
    scop = pet_scop_free(scop);
}
Scop::Scop(const Scop &other) : scop(other.scop) {}
Scop &
Scop::operator=(const Scop &other) {
  scop = other.scop;
  return *this;
}
Scop::Scop(Scop &&other) : scop(other.scop) {}
Scop &
Scop::operator=(Scop &&other) {
  scop = other.scop;
  other.scop = nullptr;
  return *this;
}

std::string
Scop::to_string() {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  std::string result = isl_schedule_to_str(sched);
  isl_schedule_free(sched);
  return result;
}
