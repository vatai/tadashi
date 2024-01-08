#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <map>

#include <isl/ast.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <pet.h>
#include <vector>

struct node_t {
  size_t parent;
  size_t id;
};

std::vector<node_t> NODES;

typedef std::pair<isl_size, isl_size> depth_position_t;
typedef std::map<depth_position_t, size_t> map_deppos2idx_t;
map_deppos2idx_t DEPPOS2IDX;

depth_position_t _get_depth_position(isl_schedule_node *node) {
  isl_size pos = 0;
  if (isl_schedule_node_has_parent(node))
    pos = isl_schedule_node_get_child_position(node);
  isl_size dep = isl_schedule_node_get_tree_depth(node);
  return {dep, pos};
}

isl_bool foreach_node(isl_schedule_node *node, void *user) {
  size_t id = NODES.size();
  depth_position_t dp = _get_depth_position(node);
  DEPPOS2IDX[dp] = id;
  printf("DEPPOS2IDX[%d, %d] = %ld\n", dp.first, dp.second, id);
  if (!isl_schedule_node_has_parent(node)) {
    NODES.push_back({.parent = -1lu, .id = id});
    printf("add(parent=-1, id=%lu)\n", id);
    printf("---\n");
    return isl_bool_true;
  }
  node = isl_schedule_node_parent(node); // go to parent
  map_deppos2idx_t::iterator parent;
  parent = DEPPOS2IDX.find(_get_depth_position(node));
  assert(parent != DEPPOS2IDX.end());
  node = isl_schedule_node_child(node, dp.second); // return from parent
  NODES.push_back({.parent = parent->second, .id = id});
  printf("add(parent=%lu, id=%lu)\n", parent->second, id);
  printf("---\n");
  return isl_bool_true;
}

isl_bool foreach_node_old(isl_schedule_node *node, void *user) {
  size_t id = NODES.size() * 100;
  size_t parent_it = -1;
  depth_position_t dp = _get_depth_position(node);
  DEPPOS2IDX[dp] = id;
  printf("%d, %d = %ld\n", dp.first, dp.second, id);
  if (isl_schedule_node_has_parent(node)) {
    node = isl_schedule_node_parent(node);
    map_deppos2idx_t::iterator parent;
    parent = DEPPOS2IDX.find(_get_depth_position(node));
    assert(parent != DEPPOS2IDX.end());
    node = isl_schedule_node_child(node, dp.second);
  }
  NODES.push_back({.parent = 0, .id = id});
  printf("---\n");
  return isl_bool_true;
}

__isl_give isl_printer *foreach_scope(__isl_take isl_printer *p, pet_scop *scop,
                                      void *user) {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_foreach_schedule_node_top_down(sched, foreach_node, user);
  isl_schedule_free(sched);
  pet_scop_free(scop);
  return p;
}

extern "C" int scan_source(char *input) { // Entry point
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");

  pet_transform_C_source(ctx, input, output, foreach_scope, NULL);

  fclose(output);
  isl_ctx_free(ctx);
  return 0;
}

/***** remove BEGIN *****/
struct cell {
  unsigned long long name;
  struct cell *next;
};

extern "C" struct cell *foo(int n) {
  struct cell *t, *first;
  first = t = (struct cell *)malloc(sizeof(struct cell));
  for (size_t i = 0; i < n; ++i) {
    t->name = i;
    t->next = (struct cell *)malloc(sizeof(struct cell));
    t = t->next;
  }
  t->name = n;
  t->next = 0;
  return first;
}

extern "C" size_t bar(struct cell *t) {
  struct cell *next;
  size_t count = 0;
  while (t) {
    next = t->next;
    free(t);
    count++;
    t = next;
  }
  return count;
}

/***** remove END *****/
