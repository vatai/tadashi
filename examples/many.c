#include <stdio.h>
#include <stdlib.h>

void init() {}
void f() {}
void g() {}

int main(int argc, char *argv[]) {
  size_t N = 100;
  double *data = malloc(N * sizeof(double));
  f();
  g();
  free(data);
  return 0;
}
