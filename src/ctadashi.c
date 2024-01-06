#include <isl/schedule.h>
#include <stdio.h>
#include <stdlib.h>

#include <isl/ctx.h>
#include <isl/printer.h>
#include <isl/schedule_node.h>
#include <pet.h>

struct node {
  struct node *parent;
  size_t id;
};

struct user_t {
  struct node *nodes;
  size_t num_nodes;
  size_t num_scopes;
  size_t allocated_nodes;
};

struct user_t *alloc_user(isl_ctx *ctx) {
  const size_t INIT_SIZE = 16;

  struct user_t *u = malloc(sizeof(*u));
  if (u == NULL)
    isl_die(ctx, isl_error_alloc, "allocation failure", return NULL);

  u->num_nodes = 0;
  u->num_scopes = 0;
  u->allocated_nodes = INIT_SIZE;
  u->nodes = malloc(sizeof(*u->nodes) * u->allocated_nodes);
  if (u->nodes == NULL) {
    free(u);
    isl_die(ctx, isl_error_alloc, "allocation failure", return NULL);
  }

  return u;
}

void maybe_realloc(struct user_t *user) {
  if (user->num_nodes < user->allocated_nodes)
    return;
  user->allocated_nodes *= 2;
  struct node *tmp;
  const size_t new_size = sizeof(*user->nodes) * user->allocated_nodes;
  tmp = realloc(user->nodes, new_size);
  if (tmp != NULL) {
    user->nodes = tmp;
    return;
  }
}

void add_node(struct user_t *user, size_t id) {
  maybe_realloc(user);
  user->nodes[user->num_nodes++].id = id;
}

void free_user(struct user_t *u) {
  free(u->nodes);
  free(u);
}

isl_bool foreach_node(isl_schedule_node *node, void *user) {
  struct user_t *u = user;
  printf("num_nodes: %lu\n", u->num_nodes);
  add_node(u, u->num_nodes);
  u->num_nodes++;
  return isl_bool_true;
}

__isl_give isl_printer *foreach_scope(__isl_take isl_printer *p, pet_scop *scop,
                                      void *user)

{
  struct user_t *u = user;
  u->num_scopes++;
  isl_schedule *sched = pet_scop_get_schedule(scop);
  isl_schedule_foreach_schedule_node_top_down(sched, foreach_node, user);
  isl_schedule_free(sched);
  pet_scop_free(scop);
  return p;
}

int scan_source(char *input) { // Entry point
  isl_ctx *ctx = isl_ctx_alloc_with_pet_options();
  FILE *output = fopen("cout.c", "w");

  struct user_t *user = alloc_user(ctx);
  pet_transform_C_source(ctx, input, output, foreach_scope, user);
  printf("Num scops: %lu\n", user->num_scopes);
  printf("Num nodes: %lu\n", user->num_nodes);
  free_user(user);

  fclose(output);
  isl_ctx_free(ctx);
  return 0;
}

/***** remove BEGIN *****/
struct cell {
  unsigned long long name;
  struct cell *next;
};

struct cell *foo(int n) {
  struct cell *t, *first;
  first = t = malloc(sizeof(struct cell));
  for (size_t i = 0; i < n; ++i) {
    t->name = i;
    t->next = malloc(sizeof(struct cell));
    t = t->next;
  }
  t->name = n;
  t->next = 0;
  return first;
}

size_t bar(struct cell *t) {
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
