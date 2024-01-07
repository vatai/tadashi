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
std::map<std::pair<isl_size, isl_size>, size_t> DEPTH_CHILDPOS_TO_INDEX;

isl_bool foreach_node(isl_schedule_node *node, void *user) {
  isl_size pos = 0;
  if (isl_schedule_node_has_parent(node))
    pos = isl_schedule_node_get_child_position(node);
  isl_size dep = isl_schedule_node_get_tree_depth(node);
  size_t id = NODES.size() * 100;
  DEPTH_CHILDPOS_TO_INDEX[{dep, pos}] = id;
  printf("%d, %d = %d\n", dep, pos, id);
  if (isl_schedule_node_has_parent(node)) {
    node = isl_schedule_node_parent(node);
    isl_size pdep = isl_schedule_node_get_tree_depth(node);
    isl_size ppos = 0;
    if (isl_schedule_node_has_parent(node))
      isl_schedule_node_get_child_position(node);
    printf("%d, %d: find: %d\n", pdep, ppos,
           DEPTH_CHILDPOS_TO_INDEX.find({pdep, ppos})->second);
    node = isl_schedule_node_child(node, pos);
  }
  NODES.push_back({0, id});
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
