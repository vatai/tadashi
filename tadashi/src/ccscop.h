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

  // template <typename Chk, typename Trn, typename... Args>
  // int
  // run_transform(Chk check_legality, Trn transform, Args &&...args) {
  //   if (this->tmp_node != nullptr)
  //     this->tmp_node = isl_schedule_node_free(this->tmp_node);
  //   tmp_node = isl_schedule_node_copy(this->current_node);
  //   this->tmp_legal = current_legal;

  //   current_node = transform(current_node, std::forward<Args>(args)...);
  //   isl_union_map *dep = isl_union_map_copy(this->dep_flow);
  //   current_legal = check_legality(current_node, dep);
  //   modified = true;
  //   return current_legal;
  // }
  // todo

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
