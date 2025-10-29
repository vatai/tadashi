#ifndef _SCOPS_H_
#define _SCOPS_H_

#include <deque>
#include <string>
#include <vector>

#include <pet.h>

#include <isl/schedule_node.h>

#include "legality.h"

class Scop {
private:
  std::vector<std::string> strings;

public:
  struct tadashi_scop *scop;
  isl_schedule_node *current_node;
  bool current_legal;
  isl_schedule_node *tmp_node;
  bool tmp_legal;
  int modified;

  Scop(pet_scop *scop);
  ~Scop();

  const char *add_string(char *str);
  const char *add_string(std::stringstream &ss);

  void rollback();
  void reset();

  template <typename Chk, typename Trn, typename... Args>
  int
  run_transform(Chk check_legality, Trn transform, Args &&...args) {
    if (tmp_node != nullptr)
      tmp_node = isl_schedule_node_free(tmp_node);
    tmp_node = isl_schedule_node_copy(current_node);
    tmp_legal = current_legal;

    current_node = transform(current_node, std::forward<Args>(args)...);

    isl_union_map *dep = isl_union_map_copy(scop->dep_flow);
    current_legal = check_legality(current_node, dep);
    modified = true;
    return current_legal;
  }
};

class Scops {

public:
  Scops(char *input, const std::vector<std::string> &defines);
  ~Scops();
  int num_scops();

public:
  isl_ctx *ctx; ///< Context for @ref Scop "Scop"s in a (Python) App object.
  std::vector<Scop *> scops;
};

#endif // _SCOPS_H_
