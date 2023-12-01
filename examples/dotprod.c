#include <stdio.h>
#include <stdlib.h>

void init_arr(size_t N, double *A) {
  for (int i = 0; i < N; ++i) {
    A[i] = random();
  }
}

const size_t N = 10;

double dotprod(size_t N, double A[N], double B[N]) {
#pragma scop
  double sum = 0.0;
  for (size_t i = 0; i < N; i++) {
    sum += A[i] * B[i];
  }
#pragma endscop
  return sum;
}

int main(int argc, char *argv[]) {
  double A[N];
  double B[N];

  init_arr(N, A);
  init_arr(N, B);
  // print_arr(N, A);
  printf("dotprod: %f\n", dotprod(N, A, B));
  return 0;
}
