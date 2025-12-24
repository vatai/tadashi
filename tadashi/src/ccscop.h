#ifndef TADASHI_SCOP_H
#define TADASHI_SCOP_H

#include <utility>

#include <isl/union_map.h>
#include <isl/union_set.h>
#include <pet.h>

class ccScop {
public:
  ccScop();
  ccScop(pet_scop *ps);

  virtual ~ccScop();
  ccScop(const ccScop &other);
  ccScop(ccScop &&other) noexcept;
  ccScop &operator=(const ccScop &other);
  ccScop &operator=(ccScop &&other) noexcept;

  void rollback();
  void reset();
  bool check_legality();

private:
  void _dealloc();
  void _copy(const ccScop &other);
  void _set_nullptr(ccScop *scop);
  void _pet_compute_live_out();
  void _pet_eliminate_dead_code();

private:
  isl_schedule *schedule;     // 1. todo maybe remove
  isl_union_map *dep_flow;    // 2. todo maybe private?
  isl_union_set *domain;      // 3.
  isl_union_set *call;        // 4.
  isl_union_map *may_writes;  // 5.
  isl_union_map *must_writes; // 6.
  isl_union_map *must_kills;  // 7.
  isl_union_map *may_reads;   // 8.
  isl_union_map *live_out;    // 9.

public:
  isl_schedule_node *current_node; // 10.
  isl_schedule_node *tmp_node;     // 11.
  bool current_legal;              // 12.
  bool tmp_legal;                  // 13.
  int modified;                    // 14.
};

#endif
