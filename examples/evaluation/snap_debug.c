#include <stdlib.h>

struct input_t {
  int n;
  int nx;
  double *array;
};
#define NANG in->n
void
fun(struct input_t *in) {
#undef NANG
  int NANG = in->n;
#pragma scop
  int i;
  for (i = 1; i < NANG; ++i) {
    in->array[i] += in->array[i - 1];
  }
  /* for (i = 1; i < in->n * in->nx; ++i) { */
  /*   in->array[i] += in->array[i - 1]; */
  /* } */
#pragma endscop
}

int
main(int argc, char *argv[]) {
  struct input_t in;
  in.n = 10000000;
  in.array = malloc(in.n * sizeof(in.array[0]));
  fun(&in);
  return 0;
}
