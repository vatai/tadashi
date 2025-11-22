#include "scop.h"

#include <iostream>
#include <string>

#include <isl/schedule.h>

Scop::Scop(pet_scop *scop) : scop(scop) {}

std::string
Scop::to_string() {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  std::string result = isl_schedule_to_str(sched);
  isl_schedule_free(sched);
  return result;
}
