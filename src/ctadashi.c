#include <stdio.h>
#include <stdlib.h>
struct cell; /* forward declaration */

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
