#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <isl/set.h>
#include <map>

#include <isl/ast.h>
#include <isl/ctx.h>
#include <isl/id.h>
#include <isl/printer.h>
#include <isl/schedule.h>
#include <isl/schedule_node.h>
#include <isl/schedule_type.h>
#include <isl/set.h>
#include <isl/union_set.h>
#include <pet.h>
#include <sstream>
#include <string>
#include <vector>

struct node_t {
  size_t parent;
  size_t id;
};

std::vector<node_t> NODES;

typedef std::pair<isl_size, isl_size> depth_position_t;
typedef std::map<depth_position_t, size_t> map_deppos2idx_t;
map_deppos2idx_t DEPPOS2IDX;

extern "C" {
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

int scan_source(char *input) { // Entry point
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");

  pet_transform_C_source(ctx, input, output, foreach_scope, NULL);

  fclose(output);
  isl_ctx_free(ctx);
  return 0;
}

std::vector<pet_scop *> SCOPS;
std::vector<isl_schedule_node *> ROOTS;

__isl_give isl_printer *get_scop(__isl_take isl_printer *p, pet_scop *scop,
                                 void *user) {
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_node *node = isl_schedule_get_root(sched);
  isl_schedule_free(sched);
  SCOPS.push_back(scop);
  ROOTS.push_back(node);
  return p;
}

int get_num_scops(char *input) { // Entry point

  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");
  // pet_options_set_autodetect(ctx, 1);
  pet_transform_C_source(ctx, input, output, get_scop, NULL);
  fclose(output);
  return SCOPS.size();
}

void free_scops() {
  if (SCOPS.size() == 0)
    return;
  isl_set *set = pet_scop_get_context(SCOPS[0]);
  isl_ctx *ctx = isl_set_get_ctx(set);
  isl_set_free(set);
  for (pet_scop *scop : SCOPS)
    pet_scop_free(scop);
  for (isl_schedule_node *root : ROOTS)
    isl_schedule_node_free(root);
  isl_ctx_free(ctx);
}

size_t num_children(size_t node_idx) {
  return isl_schedule_node_n_children(ROOTS[node_idx]);
}

size_t depth(size_t node_idx) {
  return isl_schedule_node_get_tree_depth(ROOTS[node_idx]);
}

size_t child_position(size_t node_idx) {
  return isl_schedule_node_get_child_position(ROOTS[node_idx]);
}

void child(size_t node_idx, size_t child_idx) {
  ROOTS[node_idx] = isl_schedule_node_child(ROOTS[node_idx], child_idx);
}

const char *dim_names(size_t idx) {
  isl_schedule_node *node = ROOTS[idx];
  std::stringstream ss;
  const char *name;
  isl_multi_union_pw_aff *mupa;
  mupa = isl_schedule_node_band_get_partial_schedule(node);
  name = isl_multi_union_pw_aff_get_tuple_name(mupa, isl_dim_out);
  // TODO save name
  isl_union_set *domain = isl_multi_union_pw_aff_domain(mupa);
  isl_size num_sets = isl_union_set_n_set(domain);
  isl_set_list *slist = isl_union_set_get_set_list(domain);
  for (isl_size set_idx = 0; set_idx < num_sets; set_idx++) {
    isl_set *set = isl_set_list_get_at(slist, set_idx);
    isl_size num_dims = isl_set_dim(set, isl_dim_set);
    for (isl_size di = 0; di < num_dims; di++) {
      ss << isl_set_get_dim_name(set, isl_dim_set, di);
      ss << "|";
    }
    ss << ";";
    isl_set_free(set);
  }
  isl_set_list_free(slist);
  isl_union_set_free(domain);
  return ss.str().c_str();
}

} // extern "C"

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
