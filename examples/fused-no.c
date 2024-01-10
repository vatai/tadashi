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

const size_t N = 10;

void f(size_t N, double A[N], double B[N]) {
#pragma scop
  for (size_t k = 0; k < N; k++) {
    A[k] *= 2;
  }
  for (size_t i = 0; i < N; i++) {
    B[i] += 3;
    for (size_t j = 1; j < i; j++) {
      A[j] += A[j - 1];
    }
  }
#pragma endscop
}

int main(int argc, char *argv[]) {
  double A[N];
  double B[N];

  init_arr(N, A);
  init_arr(N, B);
  f(N, A, B);
  print_arr(N, A);
  print_arr(N, B);
  return 0;
}
