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
const size_t NUM_STEPS = 10;

void f(size_t N, size_t num_steps, double A[N]) {
#pragma scop
  double B[N];
  for (size_t t = 0; t < num_steps; t++) {
    for (size_t i = 1; i < N - 1; i++) {
      if (t % 2 == 0) {
        B[i] = (A[i - 1] + A[i] + A[i + 1]) / 3.0;
      } else {
        A[i] = (B[i - 1] + B[i] + B[i + 1]) / 3.0;
      }
    }
  }
#pragma endscop
}

int main(int argc, char *argv[]) {
  double A[N];

  print_arr(N, A);

  f(N, NUM_STEPS, A);

  print_arr(N, A);
  return 0;
}
