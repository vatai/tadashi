#ifndef TADASHI_SCOP_H
#define TADASHI_SCOP_H

#include <utility>

#include <isl/union_map.h>
#include <isl/union_set.h>
#include <pet.h>

class ccScop {
public:
  virtual ~ccScop();
  ccScop();
  ccScop(pet_scop *ps);
  void dealloc();
  void rollback();
  void reset();
  bool check_legality();

public:
  isl_schedule_node *current_node;
  isl_schedule_node *tmp_node;
  isl_union_map *dep_flow; // todo maybe private?
  bool current_legal;
  bool tmp_legal;
  int modified;

private:
  // pet related
  void _pet_compute_live_out();
  void _pet_eliminate_dead_code();
  isl_union_set *domain;
  isl_union_set *call;
  isl_union_map *may_writes;
  isl_union_map *must_writes;
  isl_union_map *must_kills;
  isl_union_map *may_reads;
  isl_union_map *live_out;
  isl_schedule *schedule; // todo maybe remove
  pet_scop *_pet_scop;    // todo maybe remove
};

#endif
