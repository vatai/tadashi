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

const size_t N = 9;
const size_t NUM_STEPS = 10;

void f(size_t N, double A[N]) {
#pragma scop
  size_t half_floor = N / 2;
  size_t half_ceil = N - (N / 2);
  for (size_t i = 0; i < half_ceil; i++) {
    A[2 * i] *= 2; // 0, 2, 4...
  }
  for (size_t i = 0; i < half_floor; i++) {
    A[2 * i + 1] += 3; // 1, 3, 5...
  }
#pragma endscop
}

void g(size_t N, double A[N]) {
#pragma scop
  double B[N];
  for (size_t i = 0; i < N; i++) {
    if (i % 2 == 0) {
      A[i] += 30; // 0, 2, 4...
    } else {
      A[i] *= 20; // 1, 3, 5...
    }
  }
#pragma endscop
}

int main(int argc, char *argv[]) {
  double A[N];
  for (size_t i = 0; i < N; i++) {
    A[i] = i + 1;
  }

  print_arr(N, A);

  f(N, A);
  g(N, A);

  print_arr(N, A);
  return 0;
}
