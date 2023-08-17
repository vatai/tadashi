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

void f(size_t N, double A[N][N]) {
#pragma scop
  for (size_t i = 1; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      A[i][j] = A[i][j] + A[i - 1][j];
    }
  }
#pragma endscop
}

int main(int argc, char *argv[]) {
  double A[N][N];

  for (int i = 0; i < N; ++i) {
    init_arr(N, A[i]);
    print_arr(N, A[i]);
  }
  f(N, A);
  for (int i = 0; i < N; ++i) {
    print_arr(N, A[i]);
  }
  return 0;
}
