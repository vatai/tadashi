#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

void print_arr(size_t N, double *A) {
  for (int i = 0; i < N; ++i) {
    printf("%lf, ", A[i]);
  }
  printf("\n");
}

void init_arr(size_t N, double *A) {
  for (int i = 0; i < N; ++i) {
    A[i] = random();
  }
}

#define MAIN(fn_arr)                                                           \
  int main(int argc, char *argv[]) {                                           \
    size_t N = 8;                                                              \
    double A[N];                                                               \
                                                                               \
    init_arr(N, A);                                                            \
    print_arr(N, A);                                                           \
    fn_arr(N, A);                                                              \
    print_arr(N, A);                                                           \
                                                                               \
    return 0;                                                                  \
  }
