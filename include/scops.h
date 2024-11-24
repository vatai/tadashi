#ifndef _SCOPS_H_
#define _SCOPS_H_

#include <deque>
#include <string>
#include <vector>

#include <pet.h>

#include <isl/schedule_node.h>

class Scop {
private:
  std::vector<std::string> strings;

public:
  pet_scop *scop;
  isl_union_map *dependency;
  isl_schedule_node *current_node;
  isl_schedule_node *tmp_node;
  int modified;
  Scop(pet_scop *scop);
  ~Scop();
  const char *add_string(char *str);
  const char *add_string(std::stringstream &ss);
};

class Scops {

public:
  Scops(char *input);
  ~Scops();
  int num_scops();

public:
  isl_ctx *ctx;
  std::vector<Scop> scops;
};

class ScopsPool {
private:
  std::vector<Scops *> scops_map;
  std::deque<size_t> free_indexes;
  size_t next_index = 0;

public:
  ScopsPool();
  ~ScopsPool();
  size_t add(char *input);
  void remove(size_t pool_idx);
  Scops &operator[](size_t idx);
};

#endif // _SCOPS_H_
